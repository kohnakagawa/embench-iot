/* Copyright (C) 2017 Embecosm Limited and University of Bristol

   Contributor Graham Markall <graham.markall@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

#include <support.h>
#include <stdio.h>
#include <sys/time.h>

static struct timeval start;

void
initialise_board ()
{
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
start_trigger ()
{
  gettimeofday(&start, NULL);
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
stop_trigger ()
{
  struct timeval end;
  gettimeofday(&end, NULL);

  const double dur = end.tv_sec - start.tv_sec + (end.tv_usec - start.tv_usec) * 1.0e-6;
  const double dur_ms = dur * 1.0e3;
  printf("%g\n", dur_ms);
}
