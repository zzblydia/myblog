#ifndef COMP282_DEBUG_H
#define COMP282_DEBUG_H

#include <iostream>
#include <fstream>

namespace file {
    extern std::ofstream outputFile;

    // 重载 << 运算符, 同时进行屏幕打印和文件打印
    class Cout {
    public:
        template <typename T>
        Cout& operator<<(const T& data) {
            std::cout << data;
            outputFile << data;
            return *this;
        }

        Cout& operator<<(std::ostream& (*manip)(std::ostream&)) {
            manip(std::cout);
            manip(outputFile);
            return *this;
        }
    };

    // 重载 << 运算符, 只进行文件打印
    class Fout {
    public:
        template <typename T>
        Fout& operator<<(const T& data) {
            outputFile << data;
            return *this;
        }

        Fout& operator<<(std::ostream& (*manip)(std::ostream&)) {
            manip(outputFile);
            return *this;
        }
    };

    extern Cout cout;
    extern Fout fout;
}

#endif //COMP282_DEBUG_H
