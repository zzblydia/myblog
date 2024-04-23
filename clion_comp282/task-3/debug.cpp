#include "debug.h"

namespace file {
    std::ofstream outputFile("debug.log", std::ios::app);
    Cout cout;
    Fout fout;
}