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
    Derived(int i) : Base(i), d(i * 2) {
        cout << "Constructing Derived" << endl;
    }
};

// P136 先调用基类构造函数，再调用成员对象构造函数Base(i)，最后调用派生类构造函数d(i * 2)
int main() {
    Derived ob(100);
    ob.show();
    return 0;
}