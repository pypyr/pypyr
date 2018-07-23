"""pypyr pipeline yaml definition classes - domain specific language"""

import logging
import pypyr.moduleloader

# use pypyr logger to ensure loglevel is set correctly
logger = logging.getLogger(__name__)


class Step(object):
    """A step, as interpreted by the pypyr pipeline definition yaml.

    Encapsulates useful functions for the execution of a step, and also
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

    def run_step(self, context):
        """Run a single pipeline step.

        Args:
            context: (pypyr.context.Context) The pypyr context. This arg will
                     mutate.
        """
        logger.debug("starting")
        # the in params should be added to context before step execution.
        self.set_step_input_context(context)

        # friendly reminder [] list obj (i.e empty) evals False
        if self.foreach_items:
            self.foreach_loop(context)
        else:
            # since no looping required, don't pollute output with looping info
            self.run_conditional_decorators(context)

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
