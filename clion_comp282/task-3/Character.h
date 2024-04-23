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
    std::vector<Treasure*> treasures;
    std::vector<Potion*> potions;
    std::vector<Armour*> armours;

public:
    Character(std::string name, int hitPoints);
    void setName(const std::string& newName);
    std::string getName() const;
    void setHitPoints(int newHitPoints);
    int getHitPoints() const;
    void takeHit(int damage);
    int getProtections() const;
    void addTreasure(Treasure* treasure);
    std::vector<Treasure*> getTreasures();
    void clearTreasures();
    void addPotion(Potion* potion);
    std::vector<Potion*> getPotions();
    void clearPotions();
    void addArmour(Armour* armour);
    std::vector<Armour*> getArmours() const;
    void clearArmours();
};

class Monster : public Character {
public:
    Monster(std::string name, int hitPoints);
};

class Player : public Character {
private:
    int score;
    std::vector<Weapon*> weapons;
    Location* currentLocation;

public:
    Player(std::string name, int hitPoints);
    void setScore(int newScore);
    int getScore() const;
    void setCurrentLocation(Location* newLocation);
    Location* getCurrentLocation();
    void addWeapon(Weapon* weapon);
    void clearWeapons();
    void displayItems();
    int combat(Character *character);
};

#endif
