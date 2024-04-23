// Location.h
#ifndef LOCATION_H
#define LOCATION_H

#include <string>
#include <vector>
#include "Item.h"
#include "Character.h"

class Character;
class Location {
private:
    std::string name;
    std::string description;

    std::vector<std::pair<char, Location*>> exits;
    std::vector<Character*> monsters;

    std::vector<Weapon*> weapons;
    std::vector<Potion*> potions;
    std::vector<Treasure*> treasures;

public:
    Location();
    Location(const std::string& name, const std::string& description);
    void setName(const std::string& newName);
    std::string getName() const;

    void setDescription(const std::string& newDescription);
    std::string getDescription() const;

    void addExit(char direction, Location* destination);
    void getExits() const;
    Location* getExit(char direction);
    void addMonster(Character* newMonster);
    void delMonster(Character* monsterToDelete);
    std::vector<Character*> getMonsters() const;

    void addItem(Potion* potion);
    void addItem(Weapon* weapon);
    void addItem(Treasure* treasure);
    void displayItems() const;
    void delItem(Weapon* weaponToDelete);
    void delItem(Potion* potionToDelete);
    void delItem(Treasure* treasureToDelete);

    std::vector<Weapon*> getWeapons() ;
    std::vector<Potion*> getPotions() ;
    std::vector<Treasure*> getTreasures() ;
};

#endif
