#ifndef LOGFILE_H
#define LOGFILE_H

#include <iostream>
#include <fstream>

namespace file {
    extern std::ofstream outputFile;

    // 重载 << 运算符, 同时进行屏幕打印和文件打印
    // 第一个重载的<<运算符函数是一个模板函数，它接受任意类型的数据（T类型），并将数据分别输出到标准输出流std::cout和一个名为outputFile的文件输出流中。
    // 然后返回指向当前对象的引用，以支持连续的<<操作符链式调用
    class Cout {
    public:
        template <typename T>
        Cout& operator<<(const T& data) {
            std::cout << data;
            outputFile << data;
            return *this;
        }

        // 重载后可以输出std::endl
        Cout& operator<<(std::ostream& (*manip)(std::ostream&)) {
            manip(std::cout);
            manip(outputFile);
            return *this;
        }
    };

    // 重载 << 运算符, 只进行文件打印
    // 第二个重载的<<运算符函数接受一个函数指针参数，该函数指针指向一个返回std::ostream的函数。
    // 在这里，该函数指针通常用于控制输出格式，比如std::endl用于换行。
    // 这个函数会调用传入的函数指针，分别对标准输出流std::cout和文件输出流outputFile进行操作，然后返回指向当前对象的引用，以支持链式调用
    class Fout {
    public:
        template <typename T>
        Fout& operator<<(const T& data) {
            outputFile << data;
            return *this;
        }

        // 重载后可以输出std::endl
        Fout& operator<<(std::ostream& (*manip)(std::ostream&)) {
            manip(outputFile);
            return *this;
        }
    };

    extern Cout cout;
    extern Fout fout;
}

#endif