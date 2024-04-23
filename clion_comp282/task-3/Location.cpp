// Location.cpp
#include <iostream>
#include <algorithm>
#include "Location.h"

bool compareObjects(const Item *obj1, const Item *obj2) {
    return obj1->getName() < obj2->getName();
}

Location::Location() {
    name = "";
    description = "";
}

Location::Location(const std::string &name, const std::string &description) {
    this->name = name;
    this->description = description;
}

void Location::setName(const std::string &newName) {
    name = newName;
}

std::string Location::getName() const {
    return name;
}

void Location::setDescription(const std::string &newDescription) {
    description = newDescription;
}

std::string Location::getDescription() const {
    return description;
}

void Location::addExit(char direction, Location *destination) {
    exits.push_back(std::make_pair(direction, destination));
}

void Location::addMonster(Character *newMonster) {
    monsters.push_back(newMonster);
}

void Location::delMonster(Character *monsterToDelete) {
    // Code to delete the specified monster from the monsters vector
    monsters.erase(std::remove(monsters.begin(), monsters.end(), monsterToDelete), monsters.end());
}

std::vector<Character *> Location::getMonsters() const {
    return monsters;
}

void Location::getExits() const {
    // Code to display list of exits to the player
    for (size_t i = 0; i < exits.size(); ++i) {
        cout << exits[i].first;
        if (i < exits.size() - 1) {
            cout << ", ";
        } else {
            cout << ".";
        }
    }
    cout << std::endl;
}

Location *Location::getExit(char direction) {
    for (const auto &pair: exits) {
        if (pair.first == direction) {
            return pair.second;
        }
    }
    return nullptr;
}

void Location::addItem(Potion *potion) {
    potions.push_back(potion);
}

void Location::addItem(Weapon *weapon) {
    weapons.push_back(weapon);
}

void Location::addItem(Treasure *treasure) {
    treasures.push_back(treasure);
}

void Location::addItem(Armour *armour) {
    armours.push_back(armour);
}

void Location::delItem(Weapon *weaponToDelete) {
    // Code to delete the specified weapon from the weapons vector
    weapons.erase(std::remove(weapons.begin(), weapons.end(), weaponToDelete), weapons.end());
}

void Location::delItem(Potion *potionToDelete) {
    // Code to delete the specified potion from the potions vector
    potions.erase(std::remove(potions.begin(), potions.end(), potionToDelete), potions.end());
}

void Location::delItem(Treasure *treasureToDelete) {
    // Code to delete the specified treasure from the treasures vector
    treasures.erase(std::remove(treasures.begin(), treasures.end(), treasureToDelete), treasures.end());
}

void Location::delItem(Armour *armourToDelete) {
    // Code to delete the specified armour from the armours vector
    armours.erase(std::remove(armours.begin(), armours.end(), armourToDelete), armours.end());
}

std::vector<Weapon *> Location::getWeapons() {
    return weapons;
}

std::vector<Potion *> Location::getPotions() {
    return potions;
}

std::vector<Treasure *> Location::getTreasures() {
    return treasures;
}

std::vector<Armour *> Location::getArmours() {
    return armours;
}