#!/usr/bin/env python3


__all__ = [
    'get_target_args',
    'build_benchmark_cmd',
    'decode_results',
]

import argparse
import os
from embench_core import log


def get_target_args(remnant):
    """Parse left over arguments"""
    parser = argparse.ArgumentParser(description='Get target specific args')

    parser.add_argument(
        '--emulator',
        type=str,
        required=True,
        help='emulator',
    )

    parser.add_argument(
        '--veri_args',
        type=str,
        default='-c pk',
        help='Args to pass the verilator emulator',
    )

    return parser.parse_args(remnant)


def build_benchmark_cmd(bench, args):
    """Construct the command to run the benchmark.  "args" is a
       namespace with target specific arguments"""

    emulator_path = os.path.abspath(args.emulator)

    return [emulator_path] + args.veri_args.split(' ') + [bench]


def decode_results(stdout_str, stderr_str):
    """Extract the results from the output string of the run. Return the
       elapsed time in milliseconds or zero if the run failed."""
    # Return code is in standard output. We look for the string that means we
    # hit a breakpoint on _exit, then for the string returning the value.

    try:
        dur_time = float(stdout_str)
    except ValueError as _:
        log.debug(f"parsing failed: {stdout_str}")
        return 0.0

    return dur_time
