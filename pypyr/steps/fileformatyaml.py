"""pypyr step that parses yaml for string substitutions, writes output."""
import os
import pypyr.log.logger
import ruamel.yaml as yaml

# logger means the log level will be set correctly
logger = pypyr.log.logger.get_logger(__name__)


def run_step(context):
    """Parses input yaml file and substitutes {tokens} from context.

    Loads yaml into memory to do parsing, so be aware of big files.

    Args:
        context: pypyr.context.Context. Mandatory.
                 The following context keys expected:
                - fileFormatYamlIn. mandatory. path-like.
                  Path to source file on disk.
                - fileFormatYamlOut. mandatory. path-like. Write output file to
                  here. Will create directories in path for you.

    Returns:
        None.

    Raises:
        FileNotFoundError: take a guess
        pypyr.errors.KeyNotInContextError: fileFormatYamlIn or
            fileFormatYamlOut missing in context.
        pypyr.errors.KeyInContextHasNoValueError: fileFormatYamlIn or
            fileFormatYamlOut exists but is None.
    """
    logger.debug("started")
    context.assert_keys_have_values(__name__,
                                    'fileFormatYamlIn',
                                    'fileFormatYamlOut')

    in_path = context.get_formatted('fileFormatYamlIn')
    out_path = context.get_formatted('fileFormatYamlOut')

    logger.debug(f"opening yaml source file: {in_path}")
    with open(in_path) as infile:
        payload = yaml.load(infile, Loader=yaml.RoundTripLoader)

    logger.debug(f"opening destination file for writing: {out_path}")
    os.makedirs(os.path.abspath(os.path.dirname(out_path)), exist_ok=True)
    with open(out_path, 'w') as outfile:
        formatted_iterable = context.get_formatted_iterable(payload)
        yaml.dump(formatted_iterable,
                  outfile,
                  Dumper=yaml.RoundTripDumper,
                  allow_unicode=True,
                  width=50)

    logger.info(
        f"Read {in_path} yaml, formatted contents and wrote to {out_path}")
    logger.debug("done")
