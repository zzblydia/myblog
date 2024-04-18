// Character.h
#ifndef CHARACTER_H
#define CHARACTER_H

#include <string>
#include <vector>
#include "Item.h"
#include "Location.h"

class Location;
class Character {
private:
    std::string name;
    int hitPoints;

public:
    Character();
    Character(std::string name, int hitPoints);
    void setName(const std::string& newName);
    std::string getName() const;
    void setHitPoints(int newHitPoints);
    int getHitPoints() const;
};

class Monster : public Character {
    // Additional monster-specific attributes or methods can be added here
public:
    Monster();
    Monster(std::string name, int hitPoints);
};

class Player : public Character {
private:
    int score;
    std::vector<Weapon> weapons;
    std::vector<Potion> potions;
    std::vector<Treasure> treasures;
    Location* currentLocation;

public:
    Player();
    Player(std::string name, int hitPoints);
    void setScore(int newScore);
    int getScore() const;
    void setCurrentLocation(Location* newLocation);
    Location* getCurrentLocation();
};

#endif
