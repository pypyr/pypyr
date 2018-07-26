"""pypyr pipeline yaml definition classes - domain specific language"""

import logging
from pypyr.errors import LoopMaxExhaustedError, PipelineDefinitionError
import pypyr.moduleloader
import pypyr.utils.poll

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class Step(object):
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
        """Initialize the class. No duh, huh?

        You can happily expect the initializer to initialize all
        member attributes.

        Args:
            step: a string or a dict. This is the actual step as it exists in
                  the pipeline yaml - which is to say it can just be a string
                  for a simple step, or a dict for a complex step.
        """
        logger.debug("starting")

        # defaults for decorators
        self.foreach_items = None
        self.in_parameters = None
        self.run_me = True
        self.skip_me = False
        self.swallow_me = False
        self.name = None
        self.while_decorator = None

        if isinstance(step, dict):
            self.name = step['name']
            logger.debug(f"{self.name} is complex.")

            self.in_parameters = step.get('in', None)

            # foreach: optional value. None by default.
            self.foreach_items = step.get('foreach', None)

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

        try:
            logger.debug(f"running step {self.module}")

            self.module.run_step(context)

            logger.debug(f"step {self.module} done")
        except AttributeError:
            logger.error(f"The step {self.name} doesn't have a "
                         "run_step(context) function.")
            raise

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


class WhileDecorator(object):
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
        """Initialize the class. No duh, huh?

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

            if not self.stop and not self.max:
                logger.error(f"while decorator missing both max and stop.")
                raise PipelineDefinitionError("the while decorator must have "
                                              "either max or stop, or both. "
                                              "But not neither. Note that "
                                              "setting stop: False with no "
                                              "max is an infinite loop. If "
                                              "an infinite loop is really "
                                              "what you want, set stop: "
                                              "'{ContextKeyWithFalseValue}'")
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

        stop = False

        if self.stop:
            stop = context.get_formatted_as_type(self.stop, out_type=bool)
        else:
            if not self.max:
                # the ctor already does this check, but guess theoretically
                # consumer could have messed with the props since ctor
                logger.error(f"while decorator missing both max and stop.")
                raise PipelineDefinitionError("the while decorator must have "
                                              "either max or stop, or both. "
                                              "But not neither.")

        if stop:
            # stop is already true, even before 1st loop iteration.
            logger.info(
                f"while decorator will not loop, because the stop condition "
                f"{self.stop} already evaluated to True before 1st iteration.")
        else:
            error_on_max = context.get_formatted_as_type(
                self.error_on_max, out_type=bool)
            sleep = context.get_formatted_as_type(self.sleep, out_type=float)
            if self.max:
                max = context.get_formatted_as_type(self.max, out_type=int)

                if self.stop:
                    logger.info(f"while decorator will loop {max} times, or "
                                f"until {self.stop} evaluates to True at "
                                f"{sleep}s intervals.")
                else:
                    logger.info(f"while decorator will loop {max} times "
                                f"at {sleep}s intervals.")
            else:
                max = None
                logger.info(f"while decorator will loop until {self.stop} "
                            f"evaluates to True at {sleep}s intervals.")

            if not pypyr.utils.poll.while_until_true(interval=sleep,
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
                        raise LoopMaxExhaustedError("while loop reached "
                                                    f"{max}.")
                else:
                    if self.stop and max:
                        logger.info(
                            f"while decorator looped {max} times, "
                            f"and {self.stop} never evaluated to True.")

            logger.debug("while loop done")

        logger.debug("done")
