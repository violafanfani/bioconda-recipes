#!/usr/bin/env python
#
# Wrapper script for Java Conda packages that ensures that the java runtime is invoked with the right options.
# Adapted from https://github.com/bioconda/bioconda-recipes/blob/master/recipes/peptide-shaker/peptide-shaker.py

#
# Program Parameters
#
import os
import sys
import shutil
from os import access
from os import getenv
from os import X_OK
from pathlib import Path


default_jvm_mem_opts = ["-Xms2g", "-Xmx4g"]


class TooManyJars(Exception):
    pass


# !!! End of parameter section. No user-serviceable code below this line !!!
def find_jar_file(directory):
    d = Path(directory)
    jars = list(d.glob("webin-cli-*.jar"))
    if not jars:
        raise FileNotFoundError(
            "Could not find the jar file in {}".format(str(directory))
        )
    elif len(jars) > 1:
        raise TooManyJars("Too many jar files found in {} - {}".format(directory, jars))
    else:
        return str(jars[0].resolve())


def real_dirname(path):
    """Return the symlink-resolved, canonicalized directory-portion of path."""
    return os.path.dirname(os.path.realpath(path))


def java_executable():
    """Return the executable name of the Java interpreter."""
    java_home = getenv("JAVA_HOME")
    java_bin = os.path.join("bin", "java")

    if java_home and access(os.path.join(java_home, java_bin), X_OK):
        return os.path.join(java_home, java_bin)
    else:
        return "java"


def jvm_opts(argv):
    """Construct list of Java arguments based on our argument list.

    The argument list passed in argv must not include the script name.
    The return value is a 3-tuple lists of strings of the form:
      (memory_options, prop_options, passthrough_options)
    """
    mem_opts = []
    prop_opts = []
    pass_args = []
    exec_dir = None

    for arg in argv:
        if arg.startswith("-D"):
            prop_opts.append(arg)
        elif arg.startswith("-XX"):
            prop_opts.append(arg)
        elif arg.startswith("-Xm"):
            mem_opts.append(arg)
        elif arg.startswith("--exec_dir="):
            exec_dir = arg.split("=")[1].strip('"').strip("'")
            if not os.path.exists(exec_dir):
                shutil.copytree(
                    real_dirname(sys.argv[0]), exec_dir, symlinks=False, ignore=None
                )
        else:
            pass_args.append(arg)

    # In the original shell script the test coded below read:
    #   if [ "$jvm_mem_opts" == "" ] && [ -z ${_JAVA_OPTIONS+x} ]
    # To reproduce the behaviour of the above shell code fragment
    # it is important to explictly check for equality with None
    # in the second condition, so a null envar value counts as True!

    if mem_opts == [] and getenv("_JAVA_OPTIONS") is None:
        mem_opts = default_jvm_mem_opts

    return (mem_opts, prop_opts, pass_args, exec_dir)


def main():
    java = java_executable()
    (mem_opts, prop_opts, pass_args, exec_dir) = jvm_opts(sys.argv[1:])
    jar_dir = exec_dir if exec_dir else real_dirname(sys.argv[0])
    jar_arg = "-jar"
    jar_path = find_jar_file(jar_dir)
    java_args = [java] + mem_opts + prop_opts + [jar_arg] + [jar_path] + pass_args
    command = " ".join(java_args)
    sys.exit(os.system(command))


if __name__ == "__main__":
    main()
