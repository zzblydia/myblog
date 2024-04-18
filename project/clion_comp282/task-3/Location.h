// Location.h
#ifndef LOCATION_H
#define LOCATION_H

#include <string>
#include <vector>
#include "Item.h"
#include "Character.h"

class Monster;
class Location {
private:
    std::string name;
    std::string description;
    std::vector<std::pair<char, Location*>> exits;
    std::vector<Monster*> monsters;
    std::vector<Item*> weapons;
    std::vector<Item*> potions;
    std::vector<Item*> treasures;

public:
    Location();
    Location(const std::string& name, const std::string& description);
    void setName(const std::string& newName);
    std::string getName() const;

    void setDescription(const std::string& newDescription);
    std::string getDescription() const;

    void addExit(char direction, Location* destination);
    void getExits() const;
    void addMonster(Monster* newMonster);
    void delMonster(Monster* monsterToDelete);

    void addItem(Item* item);
    void addItem(Potion* potion);
    void addItem(Weapon* weapon);
    void addItem(Treasure* treasure);
};

#endif
