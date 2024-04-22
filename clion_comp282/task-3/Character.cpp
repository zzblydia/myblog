// Character.cpp
#include <algorithm>
#include "Character.h"

// Default constructor
Character::Character() {
    name = "";
    hitPoints = 100;
}

// Parameterized constructor
Character::Character(std::string name, int hitPoints) {
    this->name = name;
    this->hitPoints = hitPoints;
}

void Character::setName(const std::string &newName) {
    name = newName;
}

std::string Character::getName() const {
    return name;
}

void Character::setHitPoints(int newHitPoints) {
    hitPoints = newHitPoints;
}

int Character::getHitPoints() const {
    return hitPoints;
}

// Implement Monster class methods
Monster::Monster() {
    Character();
}

Monster::Monster(std::string name, int hitPoints) {
    Character(name, hitPoints);
}

// Implement Player class methods
Player::Player() {
    Character();
    score = 0;
    currentLocation = nullptr;
}

Player::Player(std::string name, int hitPoints) {
    Character(name, hitPoints);
    score = 0;
    currentLocation = nullptr;
}

void Player::setScore(int newScore) {
    score = newScore;
}

int Player::getScore() const {
    return score;
}

void Player::setCurrentLocation(Location *newLocation) {
    currentLocation = newLocation;
}

Location *Player::getCurrentLocation() {
    return currentLocation;
}

void Player::addWeapon(Weapon* weapon) {
    weapons.push_back(weapon);
}
void Player::addPotion(Potion* potion) {
    potions.push_back(potion);
}
void Player::addTreasure(Treasure* treasure) {
    treasures.push_back(treasure);
}

void Player::displayItems() const {
    std::vector<std::string> weaponNames;
    for (auto weapon : weapons) {
        weaponNames.push_back(weapon->getName());
    }
    std::vector<std::string> potionNames;
    for (auto potion : potions) {
        potionNames.push_back(potion->getName());
    }
    std::vector<std::string> treasureNames;
    for (auto treasure : treasures) {
        treasureNames.push_back(treasure->getName());
    }
    std::sort(weaponNames.begin(), weaponNames.end());
    std::sort(potionNames.begin(), potionNames.end());
    std::sort(treasureNames.begin(), treasureNames.end());

    std::cout << "Weapons: ";
    for (auto weapon : weapons) {
        std::cout << weapon->getName() << " ";
    }
    std::cout << std::endl;

    std::cout << "Potions: ";
    for (auto potionName : potionNames) {
        std::cout << potionName << " ";
    }
    std::cout << std::endl;

    std::cout << "Treasures: ";
    for (auto treasureName : treasureNames) {
        std::cout << treasureName << " ";
    }
    std::cout << std::endl;
}

std::vector<Potion*> Player::getPotions() {
    return potions;
}

void Player::clearPotions() {
    potions.clear();
}

