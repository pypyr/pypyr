"""pypyr pipeline yaml definition classes - domain specific language."""

import logging
from pypyr.errors import (get_error_name,
                          LoopMaxExhaustedError,
                          PipelineDefinitionError)
import pypyr.moduleloader
from pypyr.utils import expressions, poll

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)

# ------------------------ custom yaml tags -----------------------------------


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
        return self.value

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
            return expressions.eval_string(self.value, context)
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

# ------------------------ END custom yaml tags -------------------------------


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
        self.run_me = True
        self.skip_me = False
        self.swallow_me = False
        self.name = None
        self.while_decorator = None

        if isinstance(step, dict):
            self.name = step['name']
            logger.debug(f"{self.name} is complex.")

            self.in_parameters = step.get('in', None)

            # description: optional. Write to stdout if exists and flagged.
            self.description = step.get('description', None)
            if self.description:
                logger.info(f"{self.name}: {self.description}")

            # foreach: optional value. None by default.
            self.foreach_items = step.get('foreach', None)

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

            # while: optional, defaults none.
            while_definition = step.get('while', None)
            if while_definition:
                self.while_decorator = WhileDecorator(while_definition)

        else:
            # of course, it might not be a string. in line with duck typing,
            # beg forgiveness later. as long as it loads the module, happy
            # days.
            logger.debug(f"{step} is a simple string.")
            self.name = step

        self.module = pypyr.moduleloader.get_module(self.name)
        try:
            self.run_step_function = getattr(self.module, 'run_step')
        except AttributeError:
            logger.error(f"The step {self.name} in module {self.module} "
                         "doesn't have a run_step(context) function.")
            raise

        logger.debug("done")

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
        foreach = context.get_formatted_iterable(self.foreach_items)

        foreach_length = len(foreach)

        logger.info(f"foreach decorator will loop {foreach_length} times.")

        for i in foreach:
            logger.info(f"foreach: running step {i}")
            # the iterator must be available to the step when it executes
            context['i'] = i
            # conditional operators apply to each iteration, so might be an
            # iteration run, skips or swallows.
            self.run_conditional_decorators(context)
            logger.debug(f"foreach: done step {i}")

        logger.debug(f"foreach decorator looped {foreach_length} times.")
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

        logger.debug(f"running step {self.module}")

        self.run_step_function(context)

        logger.debug(f"step {self.module} done")

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
        skip_me = context.get_formatted_as_type(self.skip_me, out_type=bool)
        swallow_me = context.get_formatted_as_type(self.swallow_me,
                                                   out_type=bool)

        if run_me:
            if not skip_me:
                try:
                    if self.retry_decorator:
                        self.retry_decorator.retry_loop(context,
                                                        self.invoke_step)
                    else:
                        self.invoke_step(context=context)
                except Exception as ex_info:
                    if swallow_me:
                        logger.error(
                            f"{self.name} Ignoring error because swallow "
                            "is True for this step.\n"
                            f"{type(ex_info).__name__}: {ex_info}")
                    else:
                        raise
            else:
                logger.info(
                    f"{self.name} not running because skip is True.")
        else:
            logger.info(f"{self.name} not running because run is False.")

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

        if self.while_decorator:
            self.while_decorator.while_loop(context,
                                            self.run_foreach_or_conditional)
        else:
            self.run_foreach_or_conditional(context)

        logger.debug("done")

    def set_step_input_context(self, context):
        """Append step's 'in' parameters to context, if they exist.

        Append the[in] dictionary to the context. This will overwrite
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
                    f"Updating context with {parameter_count} 'in' "
                    "parameters.")
                context.update(self.in_parameters)

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
        max: (int) default None. Maximum loop iterations. None is infinite.
        sleep: (float) defaults 0. Sleep in seconds between iterations.
        stop_on: (list) default None. Always stop retry on these error
                 types. None means retry on all errors.
        retry_on: (list) default None. Only retry on these error types. All
                other error types will stop retry loop. None means retry all
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
            # max: optional. defaults None.
            self.max = retry_definition.get('max', None)

            # sleep: optional. defaults 0.
            self.sleep = retry_definition.get('sleep', 0)

            # stopOn: optional. defaults None.
            self.stop_on = retry_definition.get('stopOn', None)

            # retryOn: optional. defaults None.
            self.retry_on = retry_definition.get('retryOn', None)
        else:
            # if it isn't a dict, pipeline configuration is wrong.
            logger.error(f"retry decorator definition incorrect.")
            raise PipelineDefinitionError("retry decorator must be a dict "
                                          "(i.e a map) type.")

        logger.debug("done")

    def exec_iteration(self, counter, context, step_method):
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

         Returns:
            bool. True if step execution completed without error.
                  False if error occured during step execution.

        """
        logger.debug("starting")
        context['retryCounter'] = counter

        logger.info(f"retry: running step with counter {counter}")
        try:
            step_method(context)
            result = True
        except Exception as ex_info:
            if self.max:
                if counter == self.max:
                    logger.debug(f"retry: max {counter} retries exhausted. "
                                 "raising error.")
                    # arguably shouldn't be using errs for control of flow.
                    # but would lose the err info if not, so lesser of 2 evils.
                    raise

            if self.stop_on or self.retry_on:
                error_name = get_error_name(ex_info)
                if self.stop_on:
                    formatted_stop_list = context.get_formatted_iterable(
                        self.stop_on)
                    if error_name in formatted_stop_list:
                        logger.error(f"{error_name} in stopOn. Raising error "
                                     "and exiting retry.")
                        raise
                    else:
                        logger.debug(f"{error_name} not in stopOn. Continue.")

                if self.retry_on:
                    formatted_retry_list = context.get_formatted_iterable(
                        self.retry_on)
                    if error_name not in formatted_retry_list:
                        logger.error(f"{error_name} not in retryOn. Raising "
                                     "error and exiting retry.")
                        raise
                    else:
                        logger.debug(f"{error_name} in retryOn. Retry again.")

            result = False
            logger.error(f"retry: ignoring error because retryCounter < max.\n"
                         f"{type(ex_info).__name__}: {ex_info}")

        logger.debug(f"retry: done step with counter {counter}")

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

        sleep = context.get_formatted_as_type(self.sleep, out_type=float)
        if self.max:
            max = context.get_formatted_as_type(self.max, out_type=int)

            logger.info(f"retry decorator will try {max} times at {sleep}s "
                        "intervals.")
        else:
            max = None
            logger.info(f"retry decorator will try indefinitely at {sleep}s "
                        "intervals.")

        # this will never be false. because on counter == max,
        # exec_iteration raises an exception, breaking out of the loop.
        # pragma because cov doesn't know the implied else is impossible.
        # unit test cov is 100%, though.
        if poll.while_until_true(interval=sleep,
                                 max_attempts=max)(
                self.exec_iteration)(context=context,
                                     step_method=step_method
                                     ):  # pragma: no cover
            logger.debug("retry loop complete, reporting success.")

        logger.debug("retry loop done")

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
                logger.error(f"while decorator missing both max and stop.")
                raise PipelineDefinitionError("the while decorator must have "
                                              "either max or stop, or both. "
                                              "But not neither. Note that "
                                              "setting stop: False with no "
                                              "max is an infinite loop. If "
                                              "an infinite loop is really "
                                              "what you want, set stop: False")
        else:
            # if it isn't a dict, pipeline configuration is wrong.
            logger.error(f"while decorator definition incorrect.")
            raise PipelineDefinitionError("while decorator must be a dict "
                                          "(i.e a map) type.")

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

        logger.info(f"while: running step with counter {counter}")
        step_method(context)
        logger.debug(f"while: done step {counter}")

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

        if self.stop is None and self.max is None:
            # the ctor already does this check, but guess theoretically
            # consumer could have messed with the props since ctor
            logger.error(f"while decorator missing both max and stop.")
            raise PipelineDefinitionError("the while decorator must have "
                                          "either max or stop, or both. "
                                          "But not neither.")

        error_on_max = context.get_formatted_as_type(
            self.error_on_max, out_type=bool)
        sleep = context.get_formatted_as_type(self.sleep, out_type=float)
        if self.max is None:
            max = None
            logger.info(f"while decorator will loop until {self.stop} "
                        f"evaluates to True at {sleep}s intervals.")
        else:
            max = context.get_formatted_as_type(self.max, out_type=int)

            if max < 1:
                logger.info(
                    f"max {self.max} is {max}. while only runs when max > 0.")
                logger.debug("done")
                return

            if self.stop is None:
                logger.info(f"while decorator will loop {max} times at "
                            f"{sleep}s intervals.")
            else:
                logger.info(f"while decorator will loop {max} times, or "
                            f"until {self.stop} evaluates to True at "
                            f"{sleep}s intervals.")

        if not poll.while_until_true(interval=sleep,
                                     max_attempts=max)(
                self.exec_iteration)(context=context,
                                     step_method=step_method):
            # False means loop exhausted and stop never eval-ed True.
            if error_on_max:
                logger.error(f"exhausted {max} iterations of while loop, "
                             "and errorOnMax is True.")
                if self.stop and max:
                    raise LoopMaxExhaustedError("while loop reached "
                                                f"{max} and {self.stop} "
                                                "never evaluated to True.")
                else:
                    raise LoopMaxExhaustedError(f"while loop reached {max}.")
            else:
                if self.stop and max:
                    logger.info(
                        f"while decorator looped {max} times, "
                        f"and {self.stop} never evaluated to True.")

            logger.debug("while loop done")
        else:
            logger.info(f"while loop done, stop condition {self.stop} "
                        "evaluated True.")

        logger.debug("done")
