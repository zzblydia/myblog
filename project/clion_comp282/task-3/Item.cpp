// Item.cpp
#include "Item.h"

// Item methods
std::string Item::getName() const {
    return name;
}

void Item::setName(const std::string& newName) {
    name = newName;
}

// Potion methods
int Potion::getStrength() const {
    return strength;
}

void Potion::setStrength(int newStrength) {
    strength = newStrength;
}

// Weapon methods
int Weapon::getPower() const {
    return power;
}

void Weapon::setPower(int newPower) {
    power = newPower;
}

// Treasure methods
int Treasure::getValue() const {
    return value;
}

void Treasure::setValue(int newValue) {
    value = newValue;
}
