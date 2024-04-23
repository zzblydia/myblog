#include <iostream>
#include "Location.h"
#include "Character.h"

void Welcome(Player &player, std::vector<Location *> &locations) {
    // Function to welcome the player
    std::cout
            << "Welcome to the Adventure Game. The aim is to defeat to Boss, but your score points for defeating monsters along th way."
            << std::endl;
    std::cout << "You can use the commands:" << std::endl;
    std::cout << "n, s, e, w, inventory, drink, collect, fight, quit." << std::endl << std::endl;
}

void DescribeLocation(Player &player) {
    // Function to describe the current location
    std::cout << "---" << std::endl;
    std::cout << "You are in a " << player.getCurrentLocation()->getName() << "." <<std::endl;
    std::cout << player.getCurrentLocation()->getDescription() << std::endl;
}

void DescribeExits(Player &player) {
    // Function to describe the available exits
    std::cout << "Exits are ";
    player.getCurrentLocation()->getExits();
}

void DescribeLocationItems(Location* location) {
    if (location == nullptr) {
        std::cout << "Location is null in function DescribeLocationItems" << std::endl;
        return;
    }
    // Function to describe the items in the location
    int monsterCount = location->getMonsters().size();
    if (monsterCount == 1) {
        std::cout << "the " << location->getMonsters()[0]->getName() << " is here." << std::endl;
    } else if (monsterCount > 1) {
        std::cout << "the ";
        for(int count = 0; count < monsterCount; count++) {
            std::cout << location->getMonsters()[count]->getName();
            if (count < monsterCount - 1) {
                std::cout << ", ";
            } else {
                std::cout << " are here." << std::endl;
            }
        }
    }

    int weaponCount = location->getWeapons().size();
    if (weaponCount == 1) {
        std::cout << "There is a " << location->getWeapons()[0]->getName() << " here." << std::endl;
    } else if (weaponCount > 1) {
        std::cout << "There are ";
        for(int count = 0; count < weaponCount; count++) {
            std::cout << location->getWeapons()[count]->getName();
            if (count < weaponCount - 1) {
                std::cout << ", ";
            } else {
                std::cout << " here." << std::endl;
            }
        }
    }

    int potionCount = location->getPotions().size();
    if (potionCount == 1) {
        std::cout << "There is a " << location->getPotions()[0]->getName() << " here." << std::endl;
    } else if (potionCount > 1) {
        std::cout << "There are ";
        for(int count = 0; count < potionCount; count++) {
            std::cout << location->getPotions()[count]->getName();
            if (count < potionCount - 1) {
                std::cout << ", ";
            } else {
                std::cout << " here." << std::endl;
            }
        }
    }

    int treasureCount = location->getTreasures().size();
    if (treasureCount == 1) {
        std::cout << "There is a " << location->getTreasures()[0]->getName() << " here." << std::endl;
    } else if (treasureCount > 1) {
        std::cout << "There are ";
        for(int count = 0; count < treasureCount; count++) {
            std::cout << location->getTreasures()[count]->getName();
            if (count < treasureCount - 1) {
                std::cout << ", ";
            } else {
                std::cout << " here." << std::endl;
            }
        }
    }
}

void collect(Player &player) {
    // Function to collect items in the location
    Location *currentLocation = player.getCurrentLocation();
    std::vector<Weapon*> weapons = currentLocation->getWeapons();
    for(auto & weapon : weapons) {
        player.addWeapon(weapon);
        std::cout << "You collected the " << weapon->getName() << "." << std::endl;
        currentLocation->delItem(weapon);
    }

    std::vector<Potion*> potions = currentLocation->getPotions();
    for(auto & potion : potions) {
        player.addPotion(potion);
        std::cout << "You collected the " << potion->getName() << "." << std::endl;
        currentLocation->delItem(potion);
    }

    std::vector<Treasure*> treasures = currentLocation->getTreasures();
    for(auto & treasure : treasures) {
        player.addTreasure(treasure);
        std::cout << "You collected the " << treasure->getName() << "." << std::endl;
        currentLocation->delItem(treasure);
    }
}

int main() {
    // Create locations
    Location cave, temple, dungeon, castle, clearing, hall, garden, library, forest, house, ruins, field;

    cave.setName("cave");
    cave.setDescription("You have entered a dark and mysterious cave.");
    temple.setName("temple");
    temple.setDescription("An ancient temple filled with mystical artifacts.");
    dungeon.setName("dungeon");
    dungeon.setDescription("A dark and dangerous dungeon lies ahead.");
    castle.setName("castle");
    castle.setDescription("A majestic castle with towering walls and hidden secrets.");
    clearing.setName("clearing");
    clearing.setDescription("A peaceful clearing in the midst of the forest.");
    hall.setName("hall");
    hall.setDescription("A grand hall with echoes of the past.");
    garden.setName("garden");
    garden.setDescription("A serene garden filled with colorful flowers.");
    library.setName("library");
    library.setDescription("A vast library with shelves of ancient books.");
    forest.setName("forest");
    forest.setDescription("You are surrounded by tall trees and chirping birds.");
    house.setName("house");
    house.setDescription("A cozy house with a warm fireplace.");
    ruins.setName("ruins");
    ruins.setDescription("Decaying ruins of an ancient civilization.");
    field.setName("field");
    field.setDescription("An open field with a gentle breeze.");

    // create map
    cave.addExit('E', &field);
    field.addExit('W', &cave);
    field.addExit('E', &forest);
    field.addExit('S', &dungeon);
    dungeon.addExit('N', &field);  // dungeon的北面是field
    dungeon.addExit('E', &castle);  // dungeon的东面是castle
    temple.addExit('E', &clearing);  // temple的东面是clearing
    temple.addExit('S', &forest);  // temple的南面是forest
    forest.addExit('W', &field);  // forest的西面是field
    forest.addExit('N', &temple);  // forest的北面是temple
    forest.addExit('S', &castle);  // forest的南面是castle
    castle.addExit('W', &dungeon);  // castle的西面是dungeon
    castle.addExit('N', &forest);  // castle的北面是forest
    castle.addExit('S', &ruins);  // castle的南面是ruins
    ruins.addExit('N', &castle);  // ruins的北面是castle
    clearing.addExit('W', &temple);  // clearing的西面是temple
    clearing.addExit('E', &house);  // clearing的东面是house
    house.addExit('W', &clearing);  // house的西面是clearing
    house.addExit('E', &library);  // house的东面是library
    house.addExit('S', &hall);  // house的南面是hall
    hall.addExit('N', &house);  // hall的北面是house
    hall.addExit('E', &garden);  // hall的东面是garden
    library.addExit('W', &house);  // library的西面是house
    library.addExit('S', &garden);  // library的南面是garden
    garden.addExit('W', &hall);  // garden的西面是hall
    garden.addExit('N', &library);  // garden的北面是library

    // add item
    Treasure emerald("emerald", 40);
    cave.addItem(&emerald);

    Treasure sapphire("sapphire", 40);
    field.addItem(&sapphire);
    Weapon dagger("dagger", 5);
    field.addItem(&dagger);

    Potion red("red healing", 40);
    dungeon.addItem(&red);

    Treasure diamond("diamond", 60);
    temple.addItem(&diamond);
    Weapon sword("sword", 6);
    temple.addItem(&sword);

    Treasure gold("gold ring", 60);
    castle.addItem(&gold);
    Weapon stick("stick", 1);
    castle.addItem(&stick);

    Potion purple("purple healing", 30);
    ruins.addItem(&purple);

    Weapon club("club", 3);
    clearing.addItem(&club);

    Treasure chest("treasure chest", 200);
    house.addItem(&chest);

    Treasure coins("bag of coins", 50);
    hall.addItem(&coins);
    Potion blue("blue healing", 20);
    hall.addItem(&blue);

    Treasure ruby("ruby", 10);
    garden.addItem(&ruby);
    Weapon crossbow("crossbow", 10);
    garden.addItem(&crossbow);

    // Create player
    Player player("Alice", 100);
    player.setCurrentLocation(&clearing);

    // add monster
    Monster goblin("goblin", 10);
    field.addMonster(&goblin);

    Monster zombie("zombie", 8);
    dungeon.addMonster(&zombie);

    Monster banshee("banshee", 7);
    forest.addMonster(&banshee);

    Monster vampire("vampire", 9);
    castle.addMonster(&vampire);

    Monster dragon("dragon", 15);
    ruins.addMonster(&dragon);

    Monster orc("orc", 12);
    house.addMonster(&orc);

    Monster spectre("spectre", 5);
    house.addMonster(&spectre);

    Monster ghoul("ghoul", 10);
    garden.addMonster(&ghoul);

    // create boss
    Player boss("Boss", 100);
    cave.addMonster(&boss);

    std::vector<Location *> locations = {&cave, &temple, &dungeon, &castle, &clearing, &hall, &garden, &library,
                                         &forest, &house, &ruins, &field};
    // Game Enhancements
    Potion green("green healing", 10);
    goblin.addPotion(&green);
    Treasure cup("cup", 20);
    zombie.addTreasure(&cup);
    Treasure pearl("pearl", 30);
    banshee.addTreasure(&pearl);
    Treasure Key("key", 40);
    ghoul.addTreasure(&Key);
    Treasure Book("book", 50);
    vampire.addTreasure(&Book);

    // Game logic goes here
    Welcome(player, locations);

    std::string command;
    while (true) {
        DescribeLocation(player);
        DescribeExits(player);
        DescribeLocationItems(player.getCurrentLocation());
        std::cout << ">";

        std::cin >> command;
        if (command == "quit") {
            std::cout << "Your final score is: " << player.getScore() << std::endl;
            std::cout << "Thanks for playing! Goodbye!" << std::endl;
            break;
        } else if (command == "E" || command == "W" || command == "N" || command == "S") {
            // 如果有合法的方向输入，移动到新的位置
            Location *newLocation = player.getCurrentLocation()->getExit(command[0]);
            if (newLocation != nullptr) {
                player.setCurrentLocation(newLocation);
            } else {
                std::cout << "Invalid direction! Please try again." << std::endl;
            }
        } else if (command == "collect") {
            std::cout << "Collecting items." << std::endl;
            collect(player);
        } else if (command == "inventory" || command == "inv") {
            player.displayItems();
        } else if (command == "drink") {
            for (auto &potion: player.getPotions()) {
                player.setHitPoints(player.getHitPoints() + potion->getStrength());
            }
            player.clearPotions();
        } else if (command == "fight") {
            // get the max hitpoints of the monsters in the location
            int maxHitPoints = 0;
            Character *strongestMonster = nullptr;
            for (auto &monster: player.getCurrentLocation()->getMonsters()) {
                if (monster->getHitPoints() > maxHitPoints) {
                    maxHitPoints = monster->getHitPoints();
                    strongestMonster = monster;
                }
            }
            if (strongestMonster != nullptr) {
                // fight the strongest monster
                int ret = player.combat(strongestMonster);

                if (ret == 1) {
                    // 如果击败boss
                    if (strongestMonster->getName() == "boss") {
                        std::cout << "boss over, Your final score is: " << player.getScore() << std::endl;
                        std::cout << "Thanks for playing! Goodbye!" << std::endl;
                        break;
                    } else {
                        // 击败普通怪物, 没有看到要得分
                        player.getCurrentLocation()->delMonster(strongestMonster);
                    }
                } else if (ret == -1) {
                    std::cout << "You have been defeated by the " << strongestMonster->getName() << "!" << std::endl;
                    std::cout << "Your final score is: " << player.getScore() << std::endl;
                    std::cout << "Thanks for playing! Goodbye!" << std::endl;
                    break;
                }
            } else {
                std::cout << "There are no monsters to fight!" << std::endl;
            }

        } else {
            std::cout << "Invalid direction! Please try again.." << std::endl;
        }
    }
}
