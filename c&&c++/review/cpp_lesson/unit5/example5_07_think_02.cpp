#include <iostream>
using namespace std;

class Base {
private:
    int x;
public:
    Base(int i = 0) {
        x = i;
        cout << "Constructing Base " << i << endl;
    }

    void show() {
        cout << "x = " << x << endl;
    }
};

class Derived : public Base {
private:
    Base d;
public :
    Derived(int i) : d(i * 2) {
        Base(i);
        cout << "Constructing Derived" << endl;
    }
};

// example5_07_think_02.cpp:24:14: error: declaration of 'Base i' shadows a parameter
// 这是因为Base(i)的i和派生类的构造函数的i重名了
// 在 Derived 类的构造函数中，调用了 Base(i)，这个调用并不会构造一个新的 Base 对象，而是会创建一个临时的Base对象i并立即销毁。
// 因此，Derived 类并不会正确地初始化 Base 类的成员变量 x
// 如果改为Base(a) 或者 Base a = Base(i)就可以了, 这样Base(i)的调用就是调用构造函数了.
int main() {
    Derived ob(100);
    ob.show();
    return 0;
}