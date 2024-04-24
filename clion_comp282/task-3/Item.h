// Item.h
#ifndef ITEM_H
#define ITEM_H

#include <string>

class Item {
private:
    std::string name;

public:
    Item(std::string name);

    std::string getName() const;

    void setName(const std::string &newName);
};

class Potion : public Item {
private:
    int strength;

public:
    Potion(std::string name, int strength);

    int getStrength() const;

    void setStrength(int newStrength);
};

class Weapon : public Item {
private:
    int power;

public:
    Weapon(std::string name, int power);

    int getPower() const;

    void setPower(int newPower);
};

class Treasure : public Item {
private:
    int value;

public:
    Treasure(std::string name, int value);

    int getValue() const;

    void setValue(int newValue);
};

class Armour : public Item {
private:
    int protection;
public:
    Armour(std::string name, int protection);
    int getProtection() const;
    void setProtection(int newProtection);
};

#endif
