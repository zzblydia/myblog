#include <iostream>
#include "Location.h"
#include "Character.h"

void DescribeLocation(Player &player) {
    // Function to describe the current location
    std::cout << "Your current location is: " << player.getCurrentLocation()->getName() << std::endl;
    player.getCurrentLocation()->displayItems();
}

void DescribeExits(Player &player) {
    // Function to describe the available exits
    std::cout << "Available exits: ";
    player.getCurrentLocation()->getExits();
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

    std::vector<Location*> locations = {&cave, &temple, &dungeon, &castle, &clearing, &hall, &garden, &library, &forest, &house, &ruins, &field};

    // Game logic goes here
    std::cout << "Welcome to the Adventure Game!" << std::endl;

    std::string command;
    while (true) {
        DescribeLocation(player);
        DescribeExits(player);
        std::cout << "There are monsters in rooms:" << std::endl;
        for (auto &location: locations) {
            for(auto &monster: location->getMonsters()) {
                std::cout << "You have encountered a " << monster->getName() << "!" << std::endl;
                std::cout << "You have defeated the " << monster->getName() << "!" << std::endl;
            }
        }

        std::string command;
        std::cout << "Enter a direction to go (type 'quit' to exit): ";
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
            // Add the items to the player's inventory
            Location *currentLocation = player.getCurrentLocation();
            for (auto &potion: currentLocation->getPotions()) {
                player.addPotion(potion);
                player.setScore(player.getScore() + potion->getStrength());
            }
            currentLocation->clearPotion();

            for (auto &weapon: currentLocation->getWeapons()) {
                player.addWeapon(weapon);
                player.setScore(player.getScore() + weapon->getPower());
            }
            currentLocation->clearWeapon();

            for (auto &treasure: currentLocation->getTreasures()) {
                player.addTreasure(treasure);
                player.setScore(player.getScore() + treasure->getValue());
            }
            currentLocation->clearTreasure();
        } else if (command == "inventory" || command == "inv") {
            player.displayItems();
        }
        else if (command == "drink") {
            for (auto &potion: player.getPotions()) {
                player.setHitPoints(player.getHitPoints() + potion->getStrength());
            }
            player.clearPotions();
        } else {
            std::cout << "Invalid direction! Please try again.." << std::endl;
        }
    }
    std::cout << "Locations have been created." << std::endl;
}
