// Item.h
#ifndef ITEM_H
#define ITEM_H

#include <string>

class Item {
private:
    std::string name;

public:
    std::string getName() const;
    void setName(const std::string& newName);
};

class Potion : public Item {
private:
    int strength;

public:
    int getStrength() const;
    void setStrength(int newStrength);
};

class Weapon : public Item {
private:
    int power;

public:
    int getPower() const;
    void setPower(int newPower);
};

class Treasure : public Item {
private:
    int value;

public:
    int getValue() const;
    void setValue(int newValue);
};

#endif
