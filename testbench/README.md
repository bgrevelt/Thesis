# Testbench 

A test bench for the comparisson of water column data compression algorithms. 
The test bench is run by running the run.bat or the run.sh file in the root folder.

## algorithms
This directory contains the algorithms that are provided as a reference with the test bench. With the exception of the jpeg2k library, all algorithms are general purpose and should thus be exceeded in performance by any (proper) water column data specific algorithm.
The jpeg2k algorithm is provided as a naive implementation of an algorithm that uses the Jasper library to encode water column amplitude samples as JPEG2000 images. This algorithm has not been optimized either for speed or resource usage. The library is provided as a 64-bit windows DLL for convencience, but the source files can be found in this repository if one wants to use the library on a different platform.

## Configuration
This library contains the configuration file of the test bench. The configuration file contains the settings for the test bench, including:
* The input files to use
* Which algorithms to include in a test run
* Which parameters to provide to the algorithm
* The usere defined parameters of a number of metrics

## Source
The python source code of the test bench

