// Location.cpp
#include <iostream>
#include "Location.h"

Location::Location() {
    name = "";
    description = "";
}
Location::Location(const std::string& name, const std::string& description) {
    this->name = name;
    this->description = description;
}

void Location::setName(const std::string& newName) {
    name = newName;
}

std::string Location::getName() const {
    return name;
}

void Location::setDescription(const std::string& newDescription) {
    description = newDescription;
}

std::string Location::getDescription() const {
    return description;
}

void Location::addExit(char direction, Location* destination) {
    exits.push_back(std::make_pair(direction, destination));
}

void Location::addMonster(Monster* newMonster) {
    monsters.push_back(newMonster);
}

void Location::delMonster(Monster* monsterToDelete) {
    // Code to delete the specified monster from the monsters vector
}

void Location::getExits() const {
    // Code to display list of exits to the player
    for (const auto& pair : exits) {
        char key = pair.first;
        std::cout << key << " ";
    }
    std::cout << std::endl;
}

void Location::addItem(Item* item) {
    // Code to add item to the location
}

void Location::addItem(Potion* potion) {
    potions.push_back(potion);
}

void Location::addItem(Weapon* weapon) {
    weapons.push_back(weapon);
}

void Location::addItem(Treasure* treasure) {
    treasures.push_back(treasure);
}
