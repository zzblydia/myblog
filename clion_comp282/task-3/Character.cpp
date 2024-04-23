// Character.cpp
#include <algorithm>
#include "Character.h"

// Parameterized constructor
Character::Character(std::string name, int hitPoints) {
    this->name = name;
    this->hitPoints = hitPoints;
    this->protection = 0;
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

void Character::takeHit(int damage) {
    hitPoints -= damage;
}

void Character::addArmour(Armour *armour) {
    armours.push_back(armour);
}

std::vector<Armour *> Character::getArmours() const {
    return armours;
}

int Character::getProtection() const {
    int totalProtection = 0;
    for (auto armour: armours) {
        totalProtection += armour->getProtection();
    }
    return totalProtection;
}

// Implement Monster class methods
Monster::Monster(std::string name, int hitPoints) : Character(name, hitPoints) {
}

void Monster::addTreasure(Treasure *treasure) {
    treasures.push_back(treasure);
}

void Monster::addPotion(Potion *potion) {
    potions.push_back(potion);
}

int rollDice() {
    return rand() % 6 + 1; // Generate a random number between 1 and 6
}

// Implement Player class methods
Player::Player(std::string name, int hitPoints) : Character(name, hitPoints) {
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

void Player::addWeapon(Weapon *weapon) {
    weapons.push_back(weapon);
}

void Player::addPotion(Potion *potion) {
    potions.push_back(potion);
}

void Player::addTreasure(Treasure *treasure) {
    treasures.push_back(treasure);
}

bool compareByName(Item *a, Item *b) {
    return a->getName() < b->getName();
}

void Player::displayItems() const {
    cout << "You have the following items:" << std::endl;
    cout << "===================================" << std::endl;
    cout << " Score: " << score << " Health: " << getHitPoints() << std::endl;
    cout << " Total Armour Protection: " << getProtection() << std::endl;

    std::vector<Weapon *> displayWeapons = weapons;
    std::sort(displayWeapons.begin(), displayWeapons.end(), compareByName);
    cout << "Weapons: " << std::endl;
    for (auto weapon: displayWeapons) {
        cout << " " << weapon->getName() << " (" << weapon->getPower() << ")" << std::endl;
    }

    std::vector<Potion *> displayPotions = potions;
    std::sort(displayPotions.begin(), displayPotions.end(), compareByName);
    cout << "Potions: " << std::endl;
    if (displayPotions.size()) {
        for (auto potion: displayPotions) {
            cout << " " << potion->getName() << " (" << potion->getStrength() << ")" << std::endl;
        }
    } else {
        cout << " none." << std::endl;
    }

    std::vector<Treasure *> displayTreasures = treasures;
    std::sort(displayTreasures.begin(), displayTreasures.end(), compareByName);
    cout << "Treasures: " << std::endl;
    if (displayTreasures.size()) {
        for (auto treasure: displayTreasures) {
            cout << " " << treasure->getName() << " (" << treasure->getValue() << ")" << std::endl;
        }
    } else {
        cout << " none." << std::endl;
    }

    std::vector<Armour *> displayArmours = getArmours();
    std::sort(displayArmours.begin(), displayArmours.end(), compareByName);
    cout << "Armours: " << std::endl;
    if (displayArmours.size()) {
        for (auto armour: displayArmours) {
            cout << " " << armour->getName() << " (" << armour->getProtection() << ")" << std::endl;
        }
    } else {
        cout << " none." << std::endl;
    }
}

std::vector<Potion *> Player::getPotions() {
    return potions;
}

void Player::clearPotions() {
    potions.clear();
}

// 玩家被击败, 返回-1
// 怪物被击败, 返回1
int Player::combat(Character *character) {
    cout << "Engaging the " << character->getName() << " in combat..." << std::endl;
    cout << " the " << character->getName() << " (" << character->getHitPoints() << ")" << std::endl;
    cout << "Hero vs the " << character->getName() << std::endl;

    // 选择最强武器
    int maxWeaponPower = 0;
    for (auto weapon: weapons) {
        if (weapon->getPower() > maxWeaponPower) {
            maxWeaponPower = weapon->getPower();
        }
    }

    int round = 0;
    while (getHitPoints() > 0 && character->getHitPoints() > 0) {
        round++;
        cout << "-------------------" << std::endl;
        cout << "Round " << round << std::endl;

        // Monster attacks first
        int monsterDamage = rollDice() * 2;
        takeHit(monsterDamage);

        if (getHitPoints() <= 0) {
            cout << getHitPoints() << " " << character->getHitPoints() << std::endl;
            return -1;
        }

        // Player strikes back
        int playerDamage = rollDice() + maxWeaponPower;
        // Apply player's damage to the monster
        int monsterHitPoints = character->getHitPoints() - playerDamage;
        character->setHitPoints(monsterHitPoints);

        // Check if monster is defeated
        if (monsterHitPoints <= 0) {
            cout << getHitPoints() << " " << character->getHitPoints() << std::endl;
            return 1;
        }
    }
    return 0;
}
