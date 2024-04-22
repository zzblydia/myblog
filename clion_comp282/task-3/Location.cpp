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
}

void Location::getExits() const {
    // Code to display list of exits to the player
    for (const auto &pair: exits) {
        char key = pair.first;
        std::cout << key << " ";
    }
    std::cout << std::endl;
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

void Location::displayItems() const {
    // Code to display items in the location
    if (weapons.size() == 0 && potions.size() == 0 && treasures.size() == 0) {
        return;
    } else {
        std::cout << "Items in location " << getName() << ": " << std::endl;
        for (const auto &potion: potions) {
            std::cout << "Potion: " << potion->getName() << std::endl;
        }
        for (const auto &treasure: treasures) {
            std::cout << "Treasure: " << treasure->getName() << std::endl;
        }
        for (const auto &weapon: weapons) {
            std::cout << "Weapon: " << weapon->getName() << std::endl;
        }
    }
}

const std::vector<Weapon *> Location::getWeapons() {
    return weapons;
}

const std::vector<Potion *> Location::getPotions() {
    return potions;
}

const std::vector<Treasure *> Location::getTreasures() {
    return treasures;
}

void Location::clearWeapon() {
    weapons.clear();
}
void Location::clearPotion() {
    potions.clear();
}
void Location::clearTreasure() {
    treasures.clear();
}

std::vector<Character *> Location::getMonsters() const {
    return monsters;
}
