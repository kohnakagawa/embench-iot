#!/usr/bin/env python3

# Script to build all benchmarks

# Copyright (C) 2017, 2019 Embecosm Limited
#
# Contributor: Graham Markall <graham.markall@embecosm.com>
# Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>
#
# This file is part of Embench.

# SPDX-License-Identifier: GPL-3.0-or-later

"""
Build all Embench programs.
"""


import argparse
import os
import shutil
import subprocess
import sys

sys.path.append(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pylib')
)

from embench_core import log
from embench_core import gp
from embench_core import setup_logging
from embench_core import log_args
from embench_core import find_benchmarks
from embench_core import log_benchmarks


def build_parser():
    """Build a parser for all the arguments"""
    parser = argparse.ArgumentParser(description='Build all the benchmarks')

    parser.add_argument(
        '--builddir',
        type=str,
        default='bd',
        help='Directory in which to build benchmarks and support code',
    )
    parser.add_argument(
        '--logdir',
        type=str,
        default='logs',
        help='Directory in which to store logs',
    )
    parser.add_argument(
        '--arch',
        type=str,
        required=True,
        help='The architecture for which to build',
    )
    parser.add_argument(
        '--chip',
        type=str,
        default='default',
        help='The chip for which to build',
    )
    parser.add_argument(
        '--board',
        type=str,
        default='default',
        help='The board for which to build',
    )
    parser.add_argument('--cc', type=str, help='C compiler to use')
    parser.add_argument('--ld', type=str, help='Linker to use')
    parser.add_argument(
        '--cflags', type=str, help='Additional C compiler flags to use'
    )
    parser.add_argument(
        '--ldflags', type=str, help='Additional linker flags to use'
    )
    parser.add_argument(
        '--cc-define1-pattern',
        type=str,
        help='Pattern to define constant for compiler',
    )
    parser.add_argument(
        '--cc-define2-pattern',
        type=str,
        help='Pattern to define constant to a specific value for compiler',
    )
    parser.add_argument(
        '--cc-incdir-pattern',
        type=str,
        help='Pattern to specify include directory for the compiler',
    )
    parser.add_argument(
        '--cc-input-pattern',
        type=str,
        help='Pattern to specify compiler input file',
    )
    parser.add_argument(
        '--cc-output-pattern',
        type=str,
        help='Pattern to specify compiler output file',
    )
    parser.add_argument(
        '--ld-input-pattern',
        type=str,
        help='Pattern to specify linker input file',
    )
    parser.add_argument(
        '--ld-output-pattern',
        type=str,
        help='Pattern to specify linker output file',
    )
    parser.add_argument(
        '--user-libs', type=str, help='Additional libraries to use'
    )
    parser.add_argument(
        '--dummy-libs', type=str, help='Dummy libraries to build and link'
    )
    parser.add_argument(
        '--cpu-mhz', type=int, help='Processor clock speed in MHz'
    )
    parser.add_argument(
        '--warmup-heat',
        type=int,
        help='Number of warmup loops to execute before benchmark',
    )
    parser.add_argument(
        '--clean', action='store_true', help='Rebuild everything'
    )

    return parser


def validate_args(args):
    """Check that supplied args are all valid. By definition logging is
       working when we get here. Don't bother with build directory, since
       that will be checked when we create it.

       Update the gp dictionary with all the useful info"""
    gp['configdir'] = os.path.join(gp['rootdir'], 'config')
    gp['bd_configdir'] = os.path.join(gp['bd'], 'config')

    # Architecture
    if not args.arch:
        log.error('ERROR: Null achitecture not permitted: exiting')
        sys.exit(1)

    gp['archdir'] = os.path.join(gp['configdir'], args.arch)
    gp['bd_archdir'] = os.path.join(gp['bd_configdir'], args.arch)
    if not os.path.isdir(gp['archdir']):
        log.error(f'ERROR: Architecture "{args.arch}" not found: exiting')
        sys.exit(1)
    if not os.access(gp['archdir'], os.R_OK):
        log.error(f'ERROR: Unable to read achitecture "{args.arch}": exiting')
        sys.exit(1)

    # Chip
    if not args.chip:
        log.error('ERROR: Null chip not permitted: exiting')

    gp['chipdir'] = os.path.join(gp['archdir'], 'chips', args.chip)
    gp['bd_chipdir'] = os.path.join(gp['bd_archdir'], 'chips', args.chip)
    if not os.path.isdir(gp['chipdir']):
        log.error(
            f'ERROR: Chip "{args.chip}" not found for architecture '
            + f'"{args.arch}: exiting'
        )
        sys.exit(1)
    if not os.access(gp['chipdir'], os.R_OK):
        log.error(
            f'ERROR: Unable to read chip "{args.chip}" for architecture '
            + f'"{args.arch}": exiting'
        )
        sys.exit(1)

    # Board
    if not args.board:
        log.error('ERROR: Null board not permitted: exiting')

    gp['boarddir'] = os.path.join(gp['archdir'], 'boards', args.board)
    gp['bd_boarddir'] = os.path.join(gp['bd_archdir'], 'boards', args.board)
    if not os.path.isdir(gp['boarddir']):
        log.error(
            f'ERROR: Board "{args.board}" not found for architecture '
            + f'"{args.arch}: exiting'
        )
        sys.exit(1)
    if not os.access(gp['boarddir'], os.R_OK):
        log.error(
            f'ERROR: Unable to read board "{args.board}" for architecture '
            + f'"{args.arch}": exiting'
        )
        sys.exit(1)

    # Other args validated later.


def create_builddir(builddir, clean):
    """Create the build directory, which can be relative to the current
       directory or absolute. If the "clean" is True, delete any existing
       build directory"""
    if os.path.isabs(builddir):
        gp['bd'] = builddir
    else:
        gp['bd'] = os.path.join(gp['rootdir'], builddir)

    if os.path.isdir(gp['bd']) and clean:
        try:
            shutil.rmtree(gp['bd'])
        except PermissionError:
            log.error(
                f'ERROR: Unable to clean build directory "{gp["bd"]}: '
                + 'exiting'
            )
            sys.exit(1)

    if not os.path.isdir(gp['bd']):
        try:
            os.makedirs(gp['bd'])
        except PermissionError:
            log.error(
                f'ERROR: Unable to create build directory {gp["bd"]}: exiting'
            )
            sys.exit(1)

    if not os.access(gp['bd'], os.W_OK):
        log.error(
            f'ERROR: Unable to write to build directory {gp["bd"]}, exiting'
        )
        sys.exit(1)


def populate_defaults():
    """Return a dictionary of default configuration parameters."""
    conf = {}

    conf['cc'] = 'cc'
    # ld is not set, to allow it to default to 'cc'
    conf['cflags'] = {}
    conf['ldflags'] = {}
    conf['cc_define1_pattern'] = '-D{0}'
    conf['cc_define2_pattern'] = '-D{0}={1}'
    conf['cc_incdir_pattern'] = '-I{0}'
    conf['cc_input_pattern'] = '{0}'
    conf['cc_output_pattern'] = '-o {0}'
    conf['ld_input_pattern'] = '{0}'
    conf['ld_output_pattern'] = '-o {0}'
    conf['user_libs'] = {}
    conf['dummy_libs'] = {}
    conf['cpu_mhz'] = 1
    conf['warmup_heat'] = 1

    return conf


def populate_user_commands(conf, args):
    """Populate a dictionary of configuration command parameters, "conf", from
       values supplied on the command line in the structure, "args"."""
    if args.cc:
        conf['cc'] = args.cc
    if args.ld:
        conf['ld'] = args.ld

    return conf


def populate_user_flags(conf, args):
    """Populate a dictionary of configuration flag parameters, "conf", from
       values supplied on the command line in the structure, "args"."""
    conf = {}

    if args.cflags:
        conf['cflags'] = args.cflags.split(sep=' ')
    if args.ldflags:
        conf['ldflags'] = args.ldflags.split(sep=' ')

    return conf


def populate_user_patterns(conf, args):
    """Populate a dictionary of configuration pattern parameters, "conf", from
       values supplied on the command line in the structure, "args"."""
    conf = {}

    if args.cc_define1_pattern:
        conf['cc_define1_pattern'] = args.cc_define1_pattern
    if args.cc_define2_pattern:
        conf['cc_define2_pattern'] = args.cc_define2_pattern
    if args.cc_incdir_pattern:
        conf['cc_incdir_pattern'] = args.cc_incdir_pattern
    if args.cc_input_pattern:
        conf['cc_input_pattern'] = args.cc_input_pattern
    if args.cc_output_pattern:
        conf['cc_output_pattern'] = args.cc_output_pattern
    if args.ld_input_pattern:
        conf['ld_input_pattern'] = args.ld_input_pattern
    if args.ld_output_pattern:
        conf['ld_output_pattern'] = args.ld_output_pattern

    return conf


def populate_user_libs(conf, args):
    """Populate a dictionary of configuration library parameters, "conf", from
       values supplied on the command line in the structure, "args"."""
    conf = {}

    if args.user_libs:
        conf['user_libs'] = args.user_libs.split(sep=' ')
    if args.dummy_libs:
        conf['dummy_libs'] = args.dummy_libs.split(sep=' ')

    return conf


def populate_user_defs(conf, args):
    """Populate a dictionary of configuration definition parameters, "conf", from
       values supplied on the command line in the structure, "args"."""
    conf = {}

    if args.cpu_mhz:
        conf['cpu_mhz'] = args.cpu_mhz
    if args.warmup_heat:
        conf['warmup_heat'] = args.warmup_heat

    return conf


def populate_user(args):
    """Return a dictionary of configuration parameters, from values supplied
       on the command line in the structure, "args"."""
    conf = {}

    populate_user_commands(conf, args)
    populate_user_flags(conf, args)
    populate_user_patterns(conf, args)
    populate_user_libs(conf, args)
    populate_user_defs(conf, args)

    return conf


def add_internal_flags():
    """Add internal flag values to the command line."""
    for dirname in ['supportdir', 'boarddir', 'chipdir', 'archdir']:
        flag = gp['cc_incdir_pattern'].format(gp[dirname]).split(sep=' ')
        gp['cflags'].extend(flag)

    for dirname in ['cpu_mhz', 'warmup_heat']:
        dir_u = dirname.upper()
        flagstr = gp['cc_define2_pattern'].format(dir_u, gp[dirname])
        flag = flagstr.split(sep=' ')
        gp['cflags'].extend(flag)


def validate_tools():
    """Check the compiler and linker are available."""
    # Validate C compiler
    if not shutil.which(gp['cc']):
        log.error(f'ERROR: Compiler {gp["cc"]} not found on path: exiting')
        sys.exit(1)

    # Validate linker
    if not shutil.which(gp['ld']):
        log.error(f'ERROR: Linker {gp["ld"]} not found on path: exiting')
        sys.exit(1)


def set_parameters(args):
    """Determine all remaining parameters"""
    # Directories we need
    gp['supportdir'] = os.path.join(gp['rootdir'], 'support')
    gp['bd_supportdir'] = os.path.join(gp['bd'], 'support')

    # Default values of parameters
    config = {}
    config['default'] = populate_defaults()

    # Read each config file. Note that we pass in the config file itself as
    # local dictionary, since then it won't get filled with global variables.
    for conf in ['arch', 'chip', 'board']:
        config[conf] = {}
        conf_file = os.path.join(gp[conf + 'dir'], conf + '.cfg')
        if os.path.isfile(conf_file):
            with open(conf_file) as fileh:
                try:
                    exec(fileh.read(), globals(), config[conf])
                except PermissionError:
                    log.error('ERROR: Corrupt config file {conf_file}: exiting')
                    sys.exit(1)

    # Populate user values from the command line
    config['user'] = populate_user(args)

    # Priority is in increasing priority: default, arch, chip, board,
    # user. Flags are different in that they are additive. All others later
    # values replace earlier ones.
    gp['cflags'] = []
    gp['ldflags'] = []

    for conf in ['default', 'arch', 'chip', 'board', 'user']:
        for key, val in config[conf].items():
            if (key == 'cflags') or (key == 'ldflags'):
                gp[key].extend(val)
            else:
                gp[key] = val

    # Linker should match compiler if it hasn't been set
    if 'ld' not in gp:
        gp['ld'] = gp['cc']

    # Add our own flags to the command line, then validate the tools
    add_internal_flags()
    validate_tools()


def log_parameters():
    """Record all the global parameters in the log"""
    log.debug('Global parameters')
    log.debug('=================')

    for key, val in gp.items():
        log.debug(f'{key:<21}: {val}')

    log.debug('')


def compile_file(f_root, srcdir, bindir):
    """Compile a single C file, with the given file root, "f_root", from the
       source directory, "srcdir", in to the bin directory, "bindir" using the
       general preprocessor and C compilation flags.

       Return True if the compilation success, False if it fails. Log
       everything in the event of failure"""
    abs_src = os.path.join(f'{srcdir}', f'{f_root}.c')
    abs_bin = os.path.join(f'{bindir}', f'{f_root}.o')

    # Construct the argument list
    arglist = [f'{gp["cc"]}']
    arglist.extend(gp['cflags'])
    arglist.extend(gp['cc_output_pattern'].format(f'{f_root}.o').split(sep=' '))
    arglist.extend(gp['cc_input_pattern'].format(abs_src).split(sep=' '))

    # Run the compilation, but only if the source file is newer than the
    # binary.
    succeeded = True
    res = None

    if not os.path.isfile(abs_bin) or (
            os.path.getmtime(abs_src) > os.path.getmtime(abs_bin)
    ):
        try:
            res = subprocess.run(
                arglist,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=bindir,
                timeout=5,
            )
            if res.returncode != 0:
                log.warning(
                    f'Warning: Compilation of {f_root}.c from source directory '
                    + f'{srcdir} to binary directory {bindir} failed'
                )
                succeeded = False
        except subprocess.TimeoutExpired:
            log.warning(
                f'Warning: Compilation of {f_root}.c from source directory '
                + f'{srcdir} to binary directory {bindir} timed out'
            )
            succeeded = False

    if not succeeded:
        log.debug('Args to subprocess:')
        log.debug(f'{arglist}')
        if res:
            log.debug(res.stdout.decode('utf-8'))
            log.debug(res.stderr.decode('utf-8'))

    return succeeded


def compile_benchmark(bench):
    """Compile the benchmark, "bench".

       Return True if all files compile successfully, False otherwise."""
    abs_src_b = os.path.join(gp['benchdir'], bench)
    abs_bd_b = os.path.join(gp['bd_benchdir'], bench)
    succeeded = True

    if not os.path.isdir(abs_bd_b):
        try:
            os.makedirs(abs_bd_b)
        except PermissionError:
            log.warning(
                'Warning: Unable to create build directory for '
                + f'benchmark {bench}'
            )
            return False

    # Compile each file in the benchmark
    for filename in os.listdir(abs_src_b):
        f_root, ext = os.path.splitext(filename)
        if ext == '.c':
            succeeded &= compile_file(f_root, abs_src_b, abs_bd_b)

    return succeeded


def compile_support():
    """Compile all the support code.

       Return True if all files compile successfully, False otherwise."""
    succeeded = True

    # First the general support
    if not os.path.isdir(gp['bd_supportdir']):
        try:
            os.makedirs(gp['bd_supportdir'])
        except PermissionError:
            log.warning(
                'Warning: Unable to create support build directory '
                + f'{gp["bd_supportdir"]}'
            )
            return False

    # Compile each general support file in the benchmark
    succeeded &= compile_file('beebsc', gp['supportdir'], gp['bd_supportdir'])
    succeeded &= compile_file('main', gp['supportdir'], gp['bd_supportdir'])

    # Compile dummy files that are needed
    for dlib in gp['dummy_libs']:
        succeeded &= compile_file(
            'dummy-' + dlib, gp['supportdir'], gp['bd_supportdir']
        )

    # Compile architecture, chip and board specific files.  Note that we only
    # create the build directory if it is needed here.
    for dirname in ['arch', 'chip', 'board']:
        filename = os.path.join(gp[dirname + 'dir'], dirname + 'support.c')
        if os.path.isfile(filename):
            # Create build directory
            builddir = gp['bd_' + dirname + 'dir']
            if not os.path.isdir(builddir):
                try:
                    os.makedirs(builddir)
                except PermissionError:
                    log.warning(
                        'Warning: Unable to create build directory '
                        + f'for {dirname}, "{builddir}'
                    )
                    return False

            succeeded &= compile_file(
                dirname + 'support',
                gp[dirname + 'dir'],
                gp['bd_' + dirname + 'dir'],
            )

    return succeeded


def create_link_binlist(abs_bd):
    """Create a list of all the binaries to be linked, including those in the
       specified absolute directory, abs_bd.  The binaries in this directory
       can be specified as relative filenames.  All others will all be
       absolute addresses, since ultimately we will link in the abs_bd
       directory.  Return the result binlist, or an empty list on failure."""
    binlist = []
    for binf in os.listdir(abs_bd):
        if binf.endswith('.o'):
            binlist.extend(gp['ld_input_pattern'].format(binf).split(sep=' '))

    # Add arch, chip and board binaries
    for dirname in ['arch', 'chip', 'board']:
        binf = os.path.join(gp[f'bd_{dirname}dir'], f'{dirname}support.o')
        if os.path.isfile(binf):
            binlist.extend(gp['ld_input_pattern'].format(binf).split(sep=' '))

    # Add generic support
    for supp in ['main', 'beebsc']:
        binf = os.path.join(gp['bd_supportdir'], f'{supp}.o')
        if os.path.isfile(binf):
            binlist.extend(gp['ld_input_pattern'].format(binf).split(sep=' '))
        else:
            log.warning(f'Warning: Unable to find support library {binf}')
            return []

    # Add dummy binaries
    for dlib in gp['dummy_libs']:
        binf = os.path.join(gp['bd_supportdir'], f'dummy-{dlib}.o')
        if os.path.isfile(binf):
            binlist.extend(gp['ld_input_pattern'].format(binf).split(sep=' '))
        else:
            log.warning(f'Warning: Unable to find dummy library {binf}')
            return []

    return binlist


def create_link_arglist(bench, binlist):
    """Create the argument list for linking benchmark, "bench", from the binaries
       in "binlist"."""
    arglist = [gp['ld']]
    arglist.extend(gp['ldflags'])
    arglist.extend(gp['ld_output_pattern'].format(bench).split(sep=' '))
    arglist.extend(binlist)
    arglist.extend(gp['user_libs'])

    return arglist


def link_benchmark(bench):
    """Link the benchmark, "bench".

       Return True if link is successful, False otherwise."""
    abs_bd_b = os.path.join(gp['bd_benchdir'], bench)

    if not os.path.isdir(abs_bd_b):
        log.warning(
            'Warning: Unable to find build directory for '
            + f'benchmark {bench}'
        )
        return False

    # Use a flag to track warnings, but keep going through warnings.
    succeeded = True

    # Create the argument list
    binlist = create_link_binlist(abs_bd_b)
    if not binlist:
        succeeded = False
    arglist = create_link_arglist(bench, binlist)

    # Run the link
    try:
        res = subprocess.run(
            arglist,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=abs_bd_b,
            timeout=5,
        )
        if res.returncode != 0:
            log.warning(f'Warning: Link of benchmark "{bench}" failed')
            succeeded = False
    except subprocess.TimeoutExpired:
        log.warning(f'Warning: link of benchmark "{bench}" timed out')
        succeeded = False

    if not succeeded:
        log.debug('Args to subprocess:')
        log.debug(f'{arglist}')
        log.debug(res.stdout.decode('utf-8'))
        log.debug(res.stderr.decode('utf-8'))

    return succeeded


def main():
    """Main program to drive building of benchmarks."""
    # Establish the root directory of the repository, since we know this file is
    # in that directory.
    gp['rootdir'] = os.path.abspath(os.path.dirname(__file__))

    # Parse arguments using standard technology
    parser = build_parser()
    args = parser.parse_args()

    # Establish logging, using "build" as the log file prefix.
    setup_logging(args.logdir, 'build')
    log_args(args)

    # Establish build directory
    create_builddir(args.builddir, args.clean)

    # Check args are OK (have to have logging and build directory set up first)
    validate_args(args)

    # Find the benchmarks
    benchmarks = find_benchmarks()
    log_benchmarks(benchmarks)

    # Establish other global parameters
    set_parameters(args)
    log_parameters()

    log.debug('General log')
    log.debug('===========')

    # Track success
    successful = compile_support()
    if successful:
        log.debug(f'Compilation of support files successful')

    for bench in benchmarks:
        res = compile_benchmark(bench)
        successful &= res
        if res:
            log.debug(f'Compilation of benchmark "{bench}" successful')
            res = link_benchmark(bench)
            successful &= res
            if res:
                log.debug(f'Linking of benchmark "{bench}" successful')
                log.info(f'{bench}')

    if successful:
        log.info('All benchmarks built successfully')


# Only run if this is the main package

if __name__ == '__main__':
    sys.exit(main())
