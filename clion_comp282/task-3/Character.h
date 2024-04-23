// Character.h
#ifndef CHARACTER_H
#define CHARACTER_H

#include <iostream>
#include <string>
#include <vector>
#include "Item.h"
#include "Location.h"

class Location;
class Character {
private:
    std::string name;
    int hitPoints;
    int protection;
    std::vector<Armour*> armours;

public:
    Character(std::string name, int hitPoints);
    void setName(const std::string& newName);
    std::string getName() const;
    void setHitPoints(int newHitPoints);
    int getHitPoints() const;
    void takeHit(int damage);
    void addArmour(Armour* armour);
    std::vector<Armour*> getArmours() const;
    int getProtection() const;
};

class Monster : public Character {
private:
    std::vector<Treasure*> treasures;
    std::vector<Potion*> potions;
public:
    Monster(std::string name, int hitPoints);
    void addTreasure(Treasure* treasure);
    void addPotion(Potion* potion);
};

class Player : public Character {
private:
    int score;
    std::vector<Weapon*> weapons;
    std::vector<Potion*> potions;
    std::vector<Treasure*> treasures;
    Location* currentLocation;

public:
    Player(std::string name, int hitPoints);
    void setScore(int newScore);
    int getScore() const;
    void setCurrentLocation(Location* newLocation);
    Location* getCurrentLocation();
    void addWeapon(Weapon* weapon);
    void addPotion(Potion* potion);
    void addTreasure(Treasure* treasure);

    // 显示物品
    void displayItems() const;

    // 访问和清理
    std::vector<Potion*> getPotions();
    void clearPotions();

    int combat(Character *character);
};

#endif
