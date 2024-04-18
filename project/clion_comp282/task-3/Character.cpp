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
