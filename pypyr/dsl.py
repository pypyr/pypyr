"""pypyr pipeline yaml definition classes - domain specific language."""
import json
import logging
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.nodes import ScalarNode
from pypyr.errors import (Call,
                          ControlOfFlowInstruction,
                          get_error_name,
                          HandledError,
                          LoopMaxExhaustedError,
                          PipelineDefinitionError,
                          Stop)
from pypyr.cache.stepcache import step_cache
from pypyr.cache.backoffcache import backoff_cache
from pypyr.utils import poll

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)

# region custom yaml tags


class SpecialTagDirective:
    """Base class for all special tag directives.

    Derive all special tag directives from this base class. Of particular
    interest is the get_value implementation.

    Derived classes MUST have the following attributes:
        - yaml_tag class variable. this is the yaml tag used to represent this
          class.
        - get_value() method override. this is what pypyr calls when applying
          formatting to this scalar.

    If your derived class wants to instantiate some instance properties, do so
    in __init__ rather than from_yaml. That way, self.value always contains the
    original, untouched scalar value.

    """

    def __init__(self, value):
        """Initialize class."""
        self.value = value

    def __bool__(self):
        """Truth testing - instance is falsy if no value."""
        return bool(self.value)

    def __str__(self):
        """Friendly string representation of instance."""
        return str(self.value)

    def __repr__(self):
        """Repr representation of instance."""
        return f'{self.__class__.__name__}({self.value!r})'

    def __eq__(self, other):
        """Equivalence over-ride."""
        return repr(self) == repr(other)

    @classmethod
    def to_yaml(cls, representer, node):
        """How to serialize this class back to yaml."""
        return representer.represent_scalar(cls.yaml_tag, node.value)

    @classmethod
    def from_yaml(cls, constructor, node):
        """Implement how to create the class from yaml representation."""
        return cls(node.value)

    def get_value(self, context=None):
        """Process the input value and return the output.

        Derived classes must provide an implementation for this method.

        This method is called by the various context get_formatted functions,
        where each special tag has its own processing rules about how to format
        values for that particular tag.
        """
        raise NotImplementedError(
            'Implement this to provide the processed value of your custom tag '
            'during formatting operations.')


class Jsonify(SpecialTagDirective):
    """Serialize context structure into a json string.

    Runs formatting substitution expressions on all formattable fields in the
    input structure.
    """

    yaml_tag = '!jsonify'

    def __init__(self, value, scalar=None):
        """Initialize class with special handling for TaggedScalar.

        Args:
            value (any): Value of yaml object. Likely CommentedMap or
                         CommentedSeq or if scalar the mapped Python type for
                         the scalar.
            scalar (TaggedScalar): If type scalar, the original constructed
                                   object. This is necessary for to_yaml
                                   serialization.
        """
        self.scalar = scalar
        self.value = value

    def __repr__(self):
        """Handle TaggedScalar specially.

        This is because original node necessary to reconstruct a TaggedScalar
        and .value gives the underlying simple type value instead.
        """
        if self.scalar:
            return (
                f'{self.__class__.__name__}({self.value!r}, {self.scalar!r})')
        else:
            return f'{self.__class__.__name__}({self.value!r})'

    @classmethod
    def from_yaml(cls, constructor, node):
        """Create the class from yaml representation."""
        for data in constructor.construct_undefined(node):
            # returns generator as a means to update the
            # returned iterator for recursive yaml refs where the node is still
            # under construction.
            pass

        if isinstance(node, ScalarNode):
            if node.style:
                # style having a value means it is quoted, i.e always a str
                # therefore don't need to go and hunt down the type
                return cls(data.value, data)

            # constructed_undefined creates all scalar as TaggedScalar, which
            # is always str. Use resolver to construct object to get it to
            # parse to the appropriate Python literal simple type.
            tag = constructor.resolver.resolve(ScalarNode,
                                               node.value,
                                               (True, False))

            scalar_node = ScalarNode(tag,
                                     node.value,
                                     start_mark=node.start_mark,
                                     end_mark=node.end_mark,
                                     style=node.style,
                                     comment=node.comment,
                                     anchor=node.anchor)

            constructed_scalar_node = constructor.construct_object(scalar_node)
            return cls(constructed_scalar_node, data)

        return cls(data)

    @classmethod
    def to_yaml(cls, representer, node):
        """Serialize this class back to yaml."""
        if isinstance(node.value, CommentedMap):
            return representer.represent_mapping(cls.yaml_tag, node.value)
        elif isinstance(node.value, CommentedSeq):
            return representer.represent_sequence(cls.yaml_tag, node.value)
        else:
            return representer.represent_tagged_scalar(node.scalar)

    def get_value(self, context):
        """Serialize self contents to json."""
        # dumps writes null if self.value is None
        return json.dumps(context.get_formatted_value(self.value))


class PyString(SpecialTagDirective):
    """py strings allow you to execute python expressions dynamically.

    A py string is defined by custom yaml tag like this:
    !py <<<your expression here>>>

    For example:
        !py key == 3

    Will return True if context['key'] is 3.

    This provides dynamic python eval of an input expression. The return is
    whatever the result of the expression is.

    Use with caution: since input_string executes any arbitrary code object
    the potential for damage is great.

    The eval uses the current context object as the namespace. This means
    if you have context['mykey'], in the input_string expression you can
    use the key directly as a variable like this: "mykey == 'mykeyvalue'".

    Unlike formatting expressions, key names do NOT go in {curlies}.

    Both __builtins__ and context are available to the eval expression.

    """

    yaml_tag = '!py'

    def get_value(self, context):
        """Run python eval on the input string."""
        if self.value:
            return context.get_eval_string(self.value)
        else:
            # Empty input raises cryptic EOF syntax err, this more human
            # friendly
            raise ValueError('!py string expression is empty. It must be a '
                             'valid python expression instead.')


class SicString(SpecialTagDirective):
    """Sic strings do not have any processing applied to them.

    If a string is NOT to have {substitutions} run on it, it's sic erat
    scriptum, i.e literal.

    A sic string looks like this:
    input_string=!sic <<your string literal here>>

    For example:
        !sic piping {key} the valleys wild

    Will return "piping {key} the valleys wild" without attempting to
    substitute {key} from context.

    """

    yaml_tag = '!sic'

    def get_value(self, context=None):
        """Simply return the string as is, the whole point of a sic string."""
        return self.value

# endregion custom yaml tags


class Step:
    """A step, as interpreted by the pypyr pipeline definition yaml.

    Encapsulates useful methods for the execution of a step, and also
    maintains state necessary to run a step. Given the need to maintain state,
    this is in a class, rather than purely functional code.

    Dynamically loads the module that the step points at, interprets the step
    decorators that modify step execution, and runs the actual step with
    appropriate error handling.

    External class consumers should probably use the run_step method. run_step
    serves as the blackbox entrypoint for this class' other methods.

    Attributes:
        name: (string) this is the step-name. equivalent to the module name of
              of the step. this module is the one dynamically loaded to
              the module attribute.
        module: (importlib module) the dynamically loaded module that the
                step will execute. this module will have the run_step
                function that implements the actual step execution.
        foreach_items: (list) defaults None. Execute step once for each item in
                    list, using iterator i.
        in_parameters: (dict) defaults None. The in step decorator - i.e dict
                       to add to context before step execution.
        run_me: (bool) defaults True. step runs if this is true.
        skip_me: (bool) defaults False. step does not run if this is true.
        swallow_me: (bool) defaults False. swallow any errors during step run
                    and continue processing if true.
        while_decorator: (WhileDecorator) defaults None. execute step in while
                         loop.

    """

    def __init__(self, step):
        """Initialize the class. No duh, huh?.

        You can happily expect the initializer to initialize all
        member attributes.

        Args:
            step: a string or a dict. This is the actual step as it exists in
                  the pipeline yaml - which is to say it can just be a string
                  for a simple step, or a dict for a complex step.
        """
        logger.debug("starting")

        # defaults for decorators
        self.description = None
        self.foreach_items = None
        self.in_parameters = None
        self.retry_decorator = None
        self.line_no = None
        self.line_col = None
        self.run_me = True
        self.skip_me = False
        self.swallow_me = False
        self.name = None
        self.while_decorator = None
        self.on_error = None

        try:
            if isinstance(step, dict):
                self._init_from_dict(step)
            else:
                # of course, it might not be a string. in line with duck
                # typing, beg forgiveness later. as long as it loads
                # the module, happy days.
                logger.debug("%s is a simple string.", step)
                self.name = step

            self.run_step_function = step_cache.get_step(self.name)
        except Exception:
            # Exceptions could also happened on the step init phase
            # (ModuleNotFound, KeyError, etc..),
            # put exception handler here because of that.
            # also handle case with missing step name
            name = f" {self.name}" if self.name else ""

            if self.line_no:
                logger.error(
                    "Error at pipeline step%s yaml line: "
                    "%d, col: %d",
                    name, self.line_no, self.line_col
                )
            else:
                logger.error(
                    "Error at pipeline step%s", name
                )
            raise

        logger.debug("done")

    def _init_from_dict(self, step):
        """Initialize the class from a dict for a complex step.

        Args:
            step: (CommentedMap/dict) This is the actual step as it
            exists in the pipeline yaml.
        """
        if hasattr(step, 'lc'):
            # line_no: optional. Has value only when the yaml
            # round trip parser is in use.
            self.line_no = step.lc.line + 1
            # line_col: optional. Has value only when the yaml
            # round trip parser is in use.
            self.line_col = step.lc.col + 1

        self.name = step.get('name', None)

        if not self.name:
            raise PipelineDefinitionError('step must have a name.')

        logger.debug("%s is complex.", self.name)

        self.in_parameters = step.get('in', None)

        # description: optional. Write to stdout if exists and flagged.
        self.description = step.get('description', None)

        # foreach: optional value. None by default.
        self.foreach_items = step.get('foreach', None)
        if self.foreach_items:
            # current item in loops
            self.for_counter = None

        # retry: optional, defaults none.
        retry_definition = step.get('retry', None)
        if retry_definition:
            self.retry_decorator = RetryDecorator(retry_definition)

        # run: optional value, true by default. Allow substitution.
        self.run_me = step.get('run', True)

        # skip: optional value, false by default. Allow substitution.
        self.skip_me = step.get('skip', False)

        # swallow: optional, defaults false. Allow substitution.
        self.swallow_me = step.get('swallow', False)

        # on_error: optional, defaults none. Allow substitution.
        self.on_error = step.get('onError', None)

        # while: optional, defaults none.
        while_definition = step.get('while', None)
        if while_definition:
            self.while_decorator = WhileDecorator(while_definition)

        logger.debug("step name: %s", self.name)

    def save_error(self, context, exception, swallowed):
        """Append step's exception information to the context.

        Append the[on_error] dictionary to the context. This will append to
        existing `runErrors` values if `runErrors` are already in there.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context.
            exception: (Exception) The error detected during step execution.
            swallowed: (bool) Whether exception was swallowed or not.
        """
        failure = {
            'name': get_error_name(exception),
            'description': str(exception),
            'customError': context.get_formatted_value(
                self.on_error
            ) if self.on_error else {},
            'line': self.line_no,
            'col': self.line_col,
            'step': self.name,
            'exception': exception,
            'swallowed': swallowed,
        }

        run_errors = context.setdefault('runErrors', [])

        run_errors.append(failure)

    def foreach_loop(self, context):
        """Run step once for each item in foreach_items.

        On each iteration, the invoked step can use context['i'] to get the
        current iterator value.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate.
        """
        logger.debug("starting")

        # Loop decorators only evaluated once, not for every step repeat
        # execution.
        foreach = context.get_formatted_value(self.foreach_items)

        iteration_count = 0

        for i in foreach:
            logger.info("foreach: running step %s", i)
            iteration_count = iteration_count + 1
            # the iterator must be available to the step when it executes
            context['i'] = i
            self.for_counter = i

            # conditional operators apply to each iteration, so might be an
            # iteration run, skips or swallows.
            self.run_conditional_decorators(context)
            logger.debug("foreach: done step %s", i)

        logger.info("foreach decorator looped %s times.", iteration_count)
        logger.debug("done")

    def invoke_step(self, context):
        """Invoke 'run_step' in the dynamically loaded step module.

        Don't invoke this from outside the Step class. Use
        pypyr.dsl.Step.run_step instead.
        invoke_step just does the bare module step invocation, it does not
        evaluate any of the decorator logic surrounding the step. So unless
        you really know what you're doing, use run_step if you intend on
        executing the step the same way pypyr does.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate.
        """
        logger.debug("starting")

        logger.debug("running step %s", self.name)

        try:
            self.run_step_function(context)
        except Call as call:
            logger.debug("call: calling %s", call.groups)
            steps_runner = context.current_pipeline.steps_runner
            try:
                steps_runner.run_step_groups(
                    groups=call.groups,
                    success_group=call.success_group,
                    failure_group=call.failure_group)
            except Exception as ex_info:
                # don't want to log error twice - would've been logged already
                # in called step-group.
                raise HandledError from ex_info
            finally:
                self.reset_context_counters(context, call)

            # py 3.9 issue with coveragepy doesn't show this as covered. it is.
            logger.debug("call: done calling %s",
                         call.groups)  # pragma: no cover

        logger.debug("step %s done", self.name)

    def reset_context_counters(self, context, call):
        """Set loop counters in context to current counters on self.

        Set the following context properties to current:
        - whileCounter
        - i
        - retryCounter

        Also resets pypyr.steps.call config. In context 'call' MUST exist,
        because this method is only meant to be called stemming from a Call
        control-of-flow instruction.

        This method exists because in nested pypyr.steps.call invocations
        the child overwrites the parent's context config and similarly nested
        loop counters get overwritten. So when the called child group is done,
        use this method will reset context to continue with the parent.

        This is necessary for nested calls in loops. A nested call step's
        context config (under key 'call') will override the parent's, so when
        the nested call finishes, in order to continue the parent call you need
        to reset the config under key 'call' to what it was before the child
        got its hands on it.

        Args:
        context: (pypyr.context.Context) The pypyr context. This arg will
                 mutate.
        call: pypyr.errors.Call The control-of-flow call instruction.

        """
        if self.while_decorator:
            while_counter = self.while_decorator.while_counter
            if context['whileCounter'] != while_counter:
                context['whileCounter'] = while_counter

        if self.foreach_items:
            # an individual item could be None, so no bool check on
            # counter itself, use foreach_items instead.
            if context['i'] != self.for_counter:
                context['i'] = self.for_counter

        if self.retry_decorator:
            retry_counter = self.retry_decorator.retry_counter
            if context['retryCounter'] != retry_counter:
                context['retryCounter'] = retry_counter

        # if call does not have a value something is seriously wrong.
        assert call.original_config[1]

        # this might be a nested call instruction, so a child call
        # might have overwritten the 'call' context item.
        if context.get(call.original_config[0]) is not call.original_config[1]:
            context[call.original_config[0]] = call.original_config[1]

    def run_conditional_decorators(self, context):
        """Evaluate the step decorators to decide whether to run step or not.

        Use pypyr.dsl.Step.run_step if you intend on executing the step the
        same way pypyr does.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate.
        """
        logger.debug("starting")

        # The decorator attributes might contain formatting expressions that
        # change whether they evaluate True or False, thus apply formatting at
        # last possible instant.
        run_me = context.get_formatted_as_type(self.run_me, out_type=bool)

        if run_me:
            skip_me = context.get_formatted_as_type(self.skip_me,
                                                    out_type=bool)

            if not skip_me:
                try:
                    if self.retry_decorator:
                        self.retry_decorator.retry_loop(context,
                                                        self.invoke_step)
                    else:
                        self.invoke_step(context=context)
                except (ControlOfFlowInstruction, Stop):
                    # Control-of-Flow/Stop are instructions to go somewhere
                    # else, not errors per se.
                    raise
                except Exception as exc_info:
                    swallow_me = context.get_formatted_as_type(
                        self.swallow_me, out_type=bool)

                    if isinstance(exc_info, HandledError):
                        exc_info = exc_info.__cause__
                    else:
                        # prevent already logged err logging twice.
                        self.save_error(
                            context=context,
                            exception=exc_info,
                            swallowed=swallow_me
                        )
                    if swallow_me:
                        logger.error(
                            "%s Ignoring error because swallow "
                            "is True for this step.\n"
                            "%s: %s",
                            self.name, get_error_name(exc_info), exc_info
                        )
                    else:
                        if self.line_no:
                            logger.error(
                                "Error while running step %s "
                                "at pipeline yaml line: %d, col: %d",
                                self.name, self.line_no, self.line_col
                            )
                        else:
                            logger.error(
                                "Error while running step %s", self.name
                            )

                        raise exc_info
            else:
                logger.info(
                    "%s not running because skip is True.", self.name)
        else:
            logger.info("%s not running because run is False.", self.name)

        logger.debug("done")

    def run_foreach_or_conditional(self, context):
        """Run the foreach sequence or the conditional evaluation.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate.
        """
        logger.debug("starting")
        # friendly reminder [] list obj (i.e empty) evals False
        if self.foreach_items:
            self.foreach_loop(context)
        else:
            # since no looping required, don't pollute output with looping info
            self.run_conditional_decorators(context)

        logger.debug("done")

    def run_step(self, context):
        """Run a single pipeline step.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate.
        """
        logger.debug("starting")

        # the in params should be added to context before step execution.
        self.set_step_input_context(context)

        # give user helpful output if step will actually run or not.
        if self.description:
            description = context.get_formatted_value(self.description)
            run_me = context.get_formatted_as_type(self.run_me, out_type=bool)

            skip_me = False

            if run_me:
                skip_me = context.get_formatted_as_type(self.skip_me,
                                                        out_type=bool)

            if run_me and not skip_me:
                logger.notify(description)
            else:
                logger.notify("(skipping): %s", description)

        if self.while_decorator:
            self.while_decorator.while_loop(context,
                                            self.run_foreach_or_conditional)
        else:
            self.run_foreach_or_conditional(context)

        # the in params should be removed from context after step execution.
        self.unset_step_input_context(context)

        logger.debug("done")

    def set_step_input_context(self, context):
        """Append step's 'in' parameters to context, if they exist.

        Append the [in] dictionary to the context. This will overwrite
        existing values if the same keys are already in there. I.e if
        in_parameters has {'eggs': 'boiled'} and key 'eggs' already
        exists in context, context['eggs'] hereafter will be 'boiled'.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context.
        """
        logger.debug("starting")
        if self.in_parameters is not None:
            parameter_count = len(self.in_parameters)
            if parameter_count > 0:
                logger.debug(
                    "Updating context with %s 'in' parameters.",
                    parameter_count,
                )
                context.update(self.in_parameters)

        logger.debug("done")

    def unset_step_input_context(self, context):
        """Remove step's 'in' parameters from context, if they exist.

        Remove the [in] dictionary from the context.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context with the [in] args removed.
        """
        logger.debug("starting")

        if self.in_parameters is not None:
            # len is O(1), so not all that unnecessarily duplicated cpu time
            parameter_count = len(self.in_parameters)
            if parameter_count > 0:
                logger.debug(
                    "Removing %s 'in' parameters from context.",
                    parameter_count,
                )
                for key in self.in_parameters:
                    # slightly unorthodox pop returning None means you don't
                    # get a KeyError if key doesn't exist. The step might have
                    # removed the key from context.
                    context.pop(key, None)

        logger.debug("done")


class RetryDecorator:
    """Retry decorator, as interpreted by the pypyr pipeline definition yaml.

    Encapsulate the methods that run a step in a retry loop, and also maintains
    state necessary to run the loop. Given the need to maintain state, this is
    in a class, rather than purely functional code.

    In a normal world, Step invokes RetryDecorator. If you run it directly,
    you're responsible for the context and surrounding control-of-flow.

    External class consumers should probably use the retry_loop method.
    retry_loop serves as the blackbox entrypoint for this class' other methods.

    Attributes:
        backoff (str): default 'fixed'. Absolute name of back-off strategy.
            Builtin strategies allow aliases like fixed, linear, jitter. Custom
            backoff should give absolute name to callable derived from
            pypyr.retries.BackoffBase.
        backoff_args (any): User provided arguments for back-off strategy.
            Likely want to use a dict here.
        jrc (float): default 0. Jitter Range Coefficient. Jitter finds a random
            value between (jrc*sleep) and (sleep).
        max (int):  default None. Maximum loop iterations. None is infinite.
        sleep (float or list[float]):  defaults 0. Sleep in seconds between
            iterations.
        sleep_max (float): default None. Maximum value for sleep if using a
            backoff strategy that calculates sleep interval. None means sleep
            can increase indefinitely.
        stop_on (list[str]): default None. Always stop retry on these error
            types. None means retry on all errors.
        retry_on (list[str]): default None. Only retry on these error types.
            All other error types will stop retry loop. None means retry all
            errors.

    """

    def __init__(self, retry_definition):
        """Initialize the class. No duh, huh.

        You can happily expect the initializer to initialize all
        member attributes.

        Args:
            retry_definition: dict. This is the actual retry definition as it
                              exists in the pipeline yaml.

        """
        logger.debug("starting")

        if isinstance(retry_definition, dict):
            # backoff: optional. defaults 'fixed' - set in retry_loop().
            self.backoff = retry_definition.get('backoff', None)

            # backoffArgs: optional.
            self.backoff_args = retry_definition.get('backoffArgs', None)

            # jrc: optional. defaults 0.
            self.jrc = retry_definition.get('jrc', 0)

            # max: optional. defaults None.
            self.max = retry_definition.get('max', None)

            # sleep: optional. defaults 0.
            self.sleep = retry_definition.get('sleep', 0)

            # sleep_max: optional. defaults None.
            self.sleep_max = retry_definition.get('sleepMax', None)

            # stopOn: optional. defaults None.
            self.stop_on = retry_definition.get('stopOn', None)

            # retryOn: optional. defaults None.
            self.retry_on = retry_definition.get('retryOn', None)
        else:
            # if it isn't a dict, pipeline configuration is wrong.
            logger.error("retry decorator definition incorrect.")
            raise PipelineDefinitionError("retry decorator must be a dict "
                                          "(i.e a map) type.")

        self.retry_counter = None

        logger.debug("done")

    def exec_iteration(self, counter, context, step_method, max):
        """Run a single retry iteration.

        This method abides by the signature invoked by poll.while_until_true,
        which is to say (counter, *args, **kwargs). In a normal execution
        chain, this method's args passed by self.retry_loop where context
        and step_method set. while_until_true injects counter as a 1st arg.

        Args:
            counter. int. loop counter, which number of iteration is this.
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context.
            step_method: (method/function) This is the method/function that
                         will execute on every loop iteration. Signature is:
                         function(context)
            max: int. Execute step_method function up to this limit

         Returns:
            bool. True if step execution completed without error.
                  False if error occured during step execution.

        """
        logger.debug("starting")
        context['retryCounter'] = counter
        self.retry_counter = counter

        logger.info("retry: running step with counter %s", counter)
        try:
            step_method(context)
            result = True
        except (ControlOfFlowInstruction, Stop):
            # Control-of-Flow/Stop are instructions to go somewhere
            # else, not errors per se.
            raise
        except Exception as ex_info:
            if max:
                if counter == max:
                    logger.debug("retry: max %s retries exhausted. "
                                 "raising error.", counter)
                    # arguably shouldn't be using errs for control of flow.
                    # but would lose the err info if not, so lesser of 2 evils.
                    raise

            if isinstance(ex_info, HandledError):
                ex_info = ex_info.__cause__

            if self.stop_on or self.retry_on:
                error_name = get_error_name(ex_info)
                if self.stop_on:
                    formatted_stop_list = context.get_formatted_value(
                        self.stop_on)
                    if error_name in formatted_stop_list:
                        logger.error("%s in stopOn. Raising error "
                                     "and exiting retry.", error_name)
                        raise
                    else:
                        logger.debug("%s not in stopOn. Continue.", error_name)

                if self.retry_on:
                    formatted_retry_list = context.get_formatted_value(
                        self.retry_on)
                    if error_name not in formatted_retry_list:
                        logger.error("%s not in retryOn. Raising "
                                     "error and exiting retry.", error_name)
                        raise
                    else:
                        logger.debug("%s in retryOn. Retry again.", error_name)

            result = False
            logger.error("retry: ignoring error because retryCounter < max.\n"
                         "%s: %s", type(ex_info).__name__, ex_info)

        logger.debug("retry: done step with counter %s", counter)

        logger.debug("done")
        return result

    def retry_loop(self, context, step_method):
        """Run step inside a retry loop.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context.
            step_method: (method/function) This is the method/function that
                         will execute on every loop iteration. Signature is:
                         function(context)

        """
        logger.debug("starting")

        context['retryCounter'] = 0
        self.retry_counter = 0

        sleep = context.get_formatted_value(self.sleep)
        backoff_name = context.get_formatted_value(
            self.backoff) if self.backoff else 'fixed'

        max_sleep = None
        if self.sleep_max:
            max_sleep = context.get_formatted_as_type(self.sleep_max,
                                                      out_type=float)

        jrc = context.get_formatted_value(self.jrc)
        backoff_args = context.get_formatted_value(self.backoff_args)

        backoff_callable = backoff_cache.get_backoff(backoff_name)(
            sleep=sleep,
            max_sleep=max_sleep,
            jrc=jrc,
            kwargs=backoff_args)

        if self.max:
            max = context.get_formatted_as_type(self.max, out_type=int)

            logger.info(
                "retry decorator will try %d times with %s backoff starting "
                "at %ss intervals.", max, backoff_name, sleep)
        else:
            max = None
            logger.info(
                "retry decorator will try indefinitely with %s backoff "
                "starting at %ss intervals.", backoff_name, sleep)

        # this will never be false. because on (counter == max) exec_iteration
        # raises an exception, breaking out of the loop.
        is_retry_ok = poll.while_until_true(interval=backoff_callable,
                                            max_attempts=max)(
            self.exec_iteration)(context=context,
                                 step_method=step_method,
                                 max=max
                                 )
        assert is_retry_ok
        logger.debug("retry loop complete, reporting success.")

        logger.debug("done")


class WhileDecorator:
    """While Decorator, as interpreted by the pypyr pipeline definition yaml.

    Encapsulate the methods that run a step in a while loop, and also maintains
    state necessary to run the loop. Given the need to maintain state, this is
    in a class, rather than purely functional code.

    In a normal world, Step invokes WhileDecorator. If you run it directly,
    you're responsible for the context and surrounding control-of-flow.

    External class consumers should probably use the while_loop method.
    while_loop serves as the blackbox entrypoint for this class' other methods.

    Attributes:
        error_on_max: (bool) defaults False. Raise error if max reached.
        max: (int) default None. Maximum loop iterations. None is infinite.
        sleep: (float) defaults 0. Sleep in seconds between iterations.
        stop:(bool) defaults None. Exit loop when stop is True.

    """

    def __init__(self, while_definition):
        """Initialize the class. No duh, huh.

        You can happily expect the initializer to initialize all
        member attributes.

        Args:
            while_definition: dict. This is the actual while definition as it
                              exists in the pipeline yaml.

        """
        logger.debug("starting")

        if isinstance(while_definition, dict):
            # errorOnMax: optional. defaults False
            self.error_on_max = while_definition.get('errorOnMax', False)

            # max: optional. defaults None.
            self.max = while_definition.get('max', None)

            # sleep: optional. defaults 0.
            self.sleep = while_definition.get('sleep', 0)

            # stop: optional. defaults None.
            self.stop = while_definition.get('stop', None)

            if self.stop is None and self.max is None:
                logger.error("while decorator missing both max and stop.")
                raise PipelineDefinitionError("the while decorator must have "
                                              "either max or stop, or both. "
                                              "But not neither. Note that "
                                              "setting stop: False with no "
                                              "max is an infinite loop. If "
                                              "an infinite loop is really "
                                              "what you want, set stop: False")
        else:
            # if it isn't a dict, pipeline configuration is wrong.
            logger.error("while decorator definition incorrect.")
            raise PipelineDefinitionError("while decorator must be a dict "
                                          "(i.e a map) type.")

        self.while_counter = None

        logger.debug("done")

    def exec_iteration(self, counter, context, step_method):
        """Run a single loop iteration.

        This method abides by the signature invoked by poll.while_until_true,
        which is to say (counter, *args, **kwargs). In a normal execution
        chain, this method's args passed by self.while_loop where context
        and step_method set. while_until_true injects counter as a 1st arg.

        Args:
            counter. int. loop counter, which number of iteration is this.
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context.
            step_method: (method/function) This is the method/function that
                         will execute on every loop iteration. Signature is:
                         function(context)

         Returns:
            bool. True if self.stop evaluates to True after step execution,
                  False otherwise.

        """
        logger.debug("starting")
        context['whileCounter'] = counter
        self.while_counter = counter

        logger.info("while: running step with counter %s", counter)
        step_method(context)
        logger.debug("while: done step %s", counter)

        result = False
        # if no stop, just iterating to max)
        if self.stop:
            # dynamically evaluate stop after step execution, since the step
            # might have changed True/False status for stop.
            result = context.get_formatted_as_type(self.stop, out_type=bool)

        logger.debug("done")
        return result

    def while_loop(self, context, step_method):
        """Run step inside a while loop.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate - after method execution will contain the new
                     updated context.
            step_method: (method/function) This is the method/function that
                         will execute on every loop iteration. Signature is:
                         function(context)

        """
        logger.debug("starting")

        context['whileCounter'] = 0
        self.while_counter = 0

        if self.stop is None and self.max is None:
            # the ctor already does this check, but guess theoretically
            # consumer could have messed with the props since ctor
            logger.error("while decorator missing both max and stop.")
            raise PipelineDefinitionError("the while decorator must have "
                                          "either max or stop, or both. "
                                          "But not neither.")

        error_on_max = context.get_formatted_as_type(
            self.error_on_max, out_type=bool)
        sleep = context.get_formatted_as_type(self.sleep, out_type=float)
        if self.max is None:
            max = None
            logger.info("while decorator will loop until %s "
                        "evaluates to True at %ss intervals.",
                        self.stop, sleep)
        else:
            max = context.get_formatted_as_type(self.max, out_type=int)

            if max < 1:
                logger.info(
                    "max %s is %s. while only runs when max > 0.",
                    self.max, max)
                logger.debug("done")
                return

            if self.stop is None:
                logger.info("while decorator will loop %s times at "
                            "%ss intervals.", max, sleep)
            else:
                logger.info("while decorator will loop %s times, or "
                            "until %s evaluates to True at "
                            "%ss intervals.", max, self.stop, sleep)

        if not poll.while_until_true(interval=sleep,
                                     max_attempts=max)(
                self.exec_iteration)(context=context,
                                     step_method=step_method):
            # False means loop exhausted and stop never eval-ed True.
            if error_on_max:
                logger.error("exhausted %s iterations of while loop, "
                             "and errorOnMax is True.", max)
                if self.stop and max:
                    raise LoopMaxExhaustedError("while loop reached "
                                                f"{max} and {self.stop} "
                                                "never evaluated to True.")
                else:
                    raise LoopMaxExhaustedError(f"while loop reached {max}.")
            else:
                if self.stop and max:
                    logger.info(
                        "while decorator looped %s times, "
                        "and %s never evaluated to True.", max, self.stop)

            logger.debug("while loop done")
        else:
            logger.info("while loop done, stop condition %s "
                        "evaluated True.", self.stop)

        logger.debug("done")
