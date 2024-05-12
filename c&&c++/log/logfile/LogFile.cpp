#include "LogFile.h"
namespace file {
    std::ofstream outputFile("debug.log", std::ios::app); // 追加模式
    Cout cout;
    Fout fout;
}