/* Copyright (C) 2017 Embecosm Limited and University of Bristol

   Contributor Graham Markall <graham.markall@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

#include <support.h>
#include <time.h>

static struct timespec start;

void
initialise_board ()
{
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
start_trigger ()
{
    clock_gettime(CLOCK_MONOTONIC, &start);
}

double as_ms(struct timespec* s, struct timespec* e) {
    return (e->tv_sec - s->tv_sec + (e->tv_nsec - s->tv_nsec) * 1.0e-9) * 1.0e3;
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
stop_trigger ()
{
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("%gms\n", as_ms(&start, &end));
}
