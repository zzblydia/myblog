// Item.cpp
#include "Item.h"

// Item methods
Item::Item(std::string name) : name(name) {}

std::string Item::getName() const {
    return name;
}

void Item::setName(const std::string &newName) {
    name = newName;
}

// Potion methods
Potion::Potion(std::string name, int strength) : Item(name), strength(strength) {}

int Potion::getStrength() const {
    return strength;
}

void Potion::setStrength(int newStrength) {
    strength = newStrength;
}

// Weapon methods
Weapon::Weapon(std::string name, int power) : Item(name), power(power) {}

int Weapon::getPower() const {
    return power;
}

void Weapon::setPower(int newPower) {
    power = newPower;
}

// Treasure methods
Treasure::Treasure(std::string name, int value) : Item(name), value(value) {}

int Treasure::getValue() const {
    return value;
}

void Treasure::setValue(int newValue) {
    value = newValue;
}

// armour methods
armour::armour(std::string name, int protection) : Item(name) {
    if (name == "gauntlet") {
        this->protection = 2;
    } else {
        this->protection = protection;
    }
}

int armour::getProtection() const {
    return protection;
}

void armour::setProtection(int newProtection) {
    protection = newProtection;
}
