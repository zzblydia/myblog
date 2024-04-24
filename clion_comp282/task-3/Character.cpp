// Character.cpp
#include <algorithm>
#include "Character.h"

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

int Character::getProtections() const {
    int totalProtection = 0;
    for (auto armour: armours) {
        totalProtection += armour->getProtection();
    }
    return totalProtection;
}

void Character::addTreasure(Treasure *treasure) {
    treasures.push_back(treasure);
}

std::vector<Treasure *> Character::getTreasures() {
    return treasures;
}

void Character::clearTreasures() {
    treasures.clear();
}

void Character::addPotion(Potion *potion) {
    potions.push_back(potion);
}

std::vector<Potion *> Character::getPotions() {
    return potions;
}

void Character::clearPotions() {
    potions.clear();
}

void Character::addArmour(Armour *armour) {
    armours.push_back(armour);
}

std::vector<Armour *> Character::getArmours() const {
    return armours;
}

void Character::clearArmours() {
    armours.clear();
}

void Character::takeHit(int damage) {
    hitPoints -= damage;
}

// Implement Monster class methods
Monster::Monster(std::string name, int hitPoints) : Character(name, hitPoints) {
}

int rollDice(int num) {
    return rand() % num + 1; // Generate a random number between 1 and num
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

void Player::clearWeapons() {
    weapons.clear();
}

bool compareByName(Item *a, Item *b) {
    return a->getName() < b->getName();
}

void Player::displayItems() {
    std::cout << "You have the following items:" << std::endl;
    std::cout << "===================================" << std::endl;
    std::cout << " Score: " << score << " Health: " << getHitPoints() << std::endl;
    std::cout << " Total Armour Protection: " << getProtections() << std::endl;

    std::vector<Weapon *> displayWeapons = weapons;
    std::sort(displayWeapons.begin(), displayWeapons.end(), compareByName);
    std::cout << "Weapons: " << std::endl;
    for (auto weapon: displayWeapons) {
        std::cout << " " << weapon->getName() << " (" << weapon->getPower() << ")" << std::endl;
    }

    std::vector<Potion *> displayPotions = getPotions();
    std::sort(displayPotions.begin(), displayPotions.end(), compareByName);
    std::cout << "Potions: " << std::endl;
    if (!displayPotions.empty()) {
        for (auto potion: displayPotions) {
            std::cout << " " << potion->getName() << " (" << potion->getStrength() << ")" << std::endl;
        }
    } else {
        std::cout << " none." << std::endl;
    }

    std::vector<Treasure *> displayTreasures = getTreasures();
    std::sort(displayTreasures.begin(), displayTreasures.end(), compareByName);
    std::cout << "Treasures: " << std::endl;
    if (!displayTreasures.empty()) {
        for (auto treasure: displayTreasures) {
            std::cout << " " << treasure->getName() << " (" << treasure->getValue() << ")" << std::endl;
        }
    } else {
        std::cout << " none." << std::endl;
    }

    std::vector<Armour *> displayArmours = getArmours();
    std::sort(displayArmours.begin(), displayArmours.end(), compareByName);
    std::cout << "Armours: " << std::endl;
    if (!displayArmours.empty()) {
        for (auto armour: displayArmours) {
            std::cout << " " << armour->getName() << " (" << armour->getProtection() << ")" << std::endl;
        }
    } else {
        std::cout << " none." << std::endl;
    }
}

// 玩家被击败, 返回-1
// 怪物被击败, 返回1
int Player::combat(Character *character) {
    std::cout << "Engaging the " << character->getName() << " in combat..." << std::endl;
    std::cout << " the " << character->getName() << " (" << character->getHitPoints() << ")" << std::endl;
    std::cout << "Hero vs the " << character->getName() << std::endl;

    // 选择最强武器
    int maxWeaponPower = 0;
    for (auto weapon: weapons) {
        if (weapon->getPower() > maxWeaponPower) {
            maxWeaponPower = weapon->getPower();
        }
    }

    // 计算玩家护甲
    int totalProtection = getProtections();

    int round = 0;
    while (getHitPoints() > 0 && character->getHitPoints() > 0) {
        round++;
        std::cout << "-------------------" << std::endl;
        std::cout << "Round " << round << std::endl;

        // Monster attacks first
        int monsterDamage = rollDice(6) * 2;
        int protection = rollDice(totalProtection); // 护甲不会被消耗
        if (monsterDamage > protection) {
            takeHit(monsterDamage - protection);
        }

        if (getHitPoints() <= 0) {
            std::cout << getHitPoints() << " " << character->getHitPoints() << std::endl;
            return -1;
        }

        // Player strikes back
        int playerDamage = rollDice(6) + maxWeaponPower;
        character->takeHit(playerDamage);

        // Check if monster is defeated
        if (character->getHitPoints() <= 0) {
            std::cout << getHitPoints() << " " << character->getHitPoints() << std::endl;
            return 1;
        }
        std::cout << getHitPoints() << " " << character->getHitPoints() << std::endl;
    }
    return 0;
}
