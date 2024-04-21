// Character.cpp
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
    // todo sort weapons, potions, treasures
    
    std::cout << "Weapons: ";
    for (auto weapon : weapons) {
        std::cout << weapon->getName() << " ";
    }
    std::cout << std::endl;

    std::cout << "Potions: ";
    for (auto potion : potions) {
        std::cout << potion->getName() << " ";
    }
    std::cout << std::endl;

    std::cout << "Treasures: ";
    for (auto treasure : treasures) {
        std::cout << treasure->getName() << " ";
    }
    std::cout << std::endl;
}

const std::vector<Potion*> Player::getPotions() {
    return potions;
}

void Player::clearPotions() {
    potions.clear();
}

