#include <iostream>

using namespace std;

class Base {
private:
    int x;
public:
    Base(int i) {
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

// 如果Base(i)改到派生类的构造函数中, 派生类的构造函数的初始化列中会调用基类的无参构造函数
// example5_07_think_01.cpp:23:29: error: no matching function for call to 'Base::Base()'
int main() {
    Derived ob(100);
    ob.show();
    return 0;
}