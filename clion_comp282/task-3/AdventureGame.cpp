#include <iostream>
#include "Location.h"
#include "Character.h"

void DescribeLocation(Player &player) {
    // Function to describe the current location
    std::cout << "Your current location is: " << player.getCurrentLocation()->getName() << std::endl;
}

void DescribeExits(Player &player) {
    // Function to describe the available exits
    std::cout << "Available exits: ";
    player.getCurrentLocation()->getExits();
}

int main() {
    // Create locations
    Location cave, temple, dungeon, castle, clearing, hall, garden, library, forest, house, ruins, field;

    cave.setName("Cave");
    cave.setDescription("You have entered a dark and mysterious cave.");
    temple.setName("Temple");
    temple.setDescription("An ancient temple filled with mystical artifacts.");
    dungeon.setName("Dungeon");
    dungeon.setDescription("A dark and dangerous dungeon lies ahead.");
    castle.setName("Castle");
    castle.setDescription("A majestic castle with towering walls and hidden secrets.");
    clearing.setName("Clearing");
    clearing.setDescription("A peaceful clearing in the midst of the forest.");
    hall.setName("Hall");
    hall.setDescription("A grand hall with echoes of the past.");
    garden.setName("Garden");
    garden.setDescription("A serene garden filled with colorful flowers.");
    library.setName("Library");
    library.setDescription("A vast library with shelves of ancient books.");
    forest.setName("Forest");
    forest.setDescription("You are surrounded by tall trees and chirping birds.");
    house.setName("House");
    house.setDescription("A cozy house with a warm fireplace.");
    ruins.setName("Ruins");
    ruins.setDescription("Decaying ruins of an ancient civilization.");
    field.setName("Field");
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

    // Create player
    Player player("Alice", 100);
    player.setCurrentLocation(&clearing);

    // Game logic goes here
    std::cout << "Welcome to the Adventure Game!" << std::endl;
    DescribeLocation(player);

    std::string command;
    while (true) {
        std::string command;
        std::cout << "Enter a command (type 'quit' to exit): ";
        std::cin >> command;

        if (command == "quit") {
            std::cout << "Your final score is: " << player.getScore() << std::endl;
            std::cout << "Thanks for playing! Goodbye!" << std::endl;
            break;
        } else if (command == "E" || command == "W" || command == "N" || command == "S") {
            // 如果有合法的方向输入，移动到新的位置
            /player.setCurrentLocation(player.getCurrentLocation()->getExit(command[0]));
        }

        DescribeLocation(player);
        DescribeExits(player);
    }


    std::cout << "Locations have been created." << std::endl;
}
