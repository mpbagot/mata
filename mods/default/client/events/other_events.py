from threading import Thread
from multiprocessing import Process, Queue
import pygame
from copy import deepcopy
import random
import time

import util
from api.item import *
from api.packets import SendCommandPacket, MountPacket, AttackPacket
from api.entity import Player, Pickup
from api.vehicle import Vehicle
from api.gui.objects import ItemSlot, ArmourSlot

from mods.default.client.events.tick_events import genWorld, handleProcess
from mods.default.items import *
from mods.default.packets import *

def onGameMouseClick(game, mousePos, pressed, event):
    """
    Event Hook: onMouseClick
    Handle a mouse click on vehicles, players and entities
    """
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:
        chatOverlay = game.getModInstance('ClientMod').chatOverlay
        pauseOverlay = game.getModInstance('ClientMod').pauseOverlay

        # Skip handling mouse clicks if 'paused' or in the chat window
        if game.getGUIState().isOverlayOpen(chatOverlay) or game.getGUIState().isOverlayOpen(pauseOverlay):
            return

        if pressed[0]:
            # Attack button (LMB) was pressed
            # Perform an attack
            weapons = [stack.getItem() for stack in game.player.inventory.getEquipped()[:2]]
            pp = game.getModInstance('ClientMod').packetPipeline
            for weapon in weapons:
                if isinstance(weapon, Weapon):
                    # Attack with this weapon
                    # Send AttackPacket so that server can run damage calculation
                    pp.sendToServer(AttackPacket(game.player.name, weapon))

                    # TODO Run the animation
                    pass

                # Attempt to punch with a fist
                elif isinstance(weapon, NullItem):
                    if random.randint(0, 5) == 3:
                        pp.sendToServer(AttackPacket(game.player.name, Teeth()))

        # Interaction button (RMB) was pressed
        elif pressed[2]:
            screen = game.getGui()[1].screen

            w = screen.get_width()
            h = screen.get_height()

            # Get the main player's position, to calculate the screen positions of the other players
            mainAbsPos = game.player.pos

            for obj in game.world.vehicles+game.world.players:
                # Get the difference in position
                deltaPos = [obj.pos[a]-mainAbsPos[a] for a in range(2)]

                # Get the object image size
                size = obj.smallImg if isinstance(obj, Player) else obj.getImage(game.modLoader.gameRegistry.resources)
                if size is None:
                    continue

                size = size.get_rect()

                # Adjust position accordingly
                pos = [w//2+deltaPos[0]*40-size.width//2, h//2+deltaPos[1]*40-size.height//2]

                # Create a rect based on the vehicle image
                rect = pygame.Rect(pos+[size.width, size.height])
                if rect.collidepoint(mousePos):
                    if isinstance(obj, Vehicle):
                        # User has clicked on the vehicle
                        # Send MountPacket to server to sync this change there.
                        packet = MountPacket(obj.uuid, game.player.name)
                        game.packetPipeline.sendToServer(packet)
                        obj.mountRider(game.player, game)

                    elif isinstance(obj, Player):
                        # User has clicked on the player
                        chatOverlay = game.getModInstance('ClientMod').chatOverlay
                        if not game.getGUIState().isOverlayOpen(chatOverlay):
                            game.openOverlay(chatOverlay, game, obj.name)
                    return

def onTradeMouseClick(game, mousePos, pressed, event):
    """
    Event Hook: onMouseClick
    Handle the movement of items between slots in the trade screen
    """
    gui = game.getGui()
    if gui and gui[0] == game.getModInstance('ClientMod').tradeGui:
        # moveItem needs to store the section of inventory, index of inv.itemSlots it is from, and the itemstack itself
        for s, slot in enumerate(gui[1].itemSlots):
            if slot.button.isHovered(mousePos):
                # If the player has clicked on a slot in the inventory
                if pressed[0]:
                    # LMB click
                    # If carrying an itemstack
                    if gui[1].moveItem:
                        stack1, stack2 = gui[1].moveItem[1].add(slot.item)
                        # Place the carried item into the clicked slot
                        gui[1].__getattribute__('inv'+str(s%2 + 1)).items['main'][s//2] = stack1
                        # game.player.inventory.items['main'][s] = stack1

                        # If clicking on a filled slot, swap or add the moveItem with
                        # the stack in the slot
                        if stack2 and stack2.getRegistryName() != 'null_item':
                            gui[1].moveItem = [s, stack2]
                        else:
                            gui[1].moveItem = None

                    # If carrying nothing
                    else:
                        # If clicking on a filled spot, pickup the item
                        if slot.item.getRegistryName() != 'null_item':
                            gui[1].moveItem = [s, slot.item]
                            gui[1].__getattribute__('inv'+str(s%2 + 1)).items['main'][s//2] = ItemStack(NullItem(), 0)
                            # game.player.inventory.items['main'][s] = ItemStack(NullItem(), 0)

                elif pressed[2]:
                    # RMB click
                    # If carrying an itemstack
                    if gui[1].moveItem:
                        if gui[1].moveItem[1].stackSize == 1 and slot.item.getRegistryName() == 'null_item':
                            # Place the carried item into the clicked slot
                            gui[1].__getattribute__('inv'+str(s%2 + 1)).items['main'][s//2] = gui[1].moveItem[1]
                            # game.player.inventory.items['main'][s] = gui[1].moveItem[1]

                            gui[1].moveItem = None
                            continue

                        gui[1].moveItem[1], one = gui[1].moveItem[1].getOne()
                        if one == slot.item:
                            stack1, stack2 = slot.item.add(one)
                            if gui[1].moveItem[2].getRegistryName() != 'null_item':
                                stack2 = gui[1].moveItem[1].add(stack2)[0]

                            if stack2 and stack2.getRegistryName() != 'null_item':
                                gui[1].moveItem = [s, stack2]
                            else:
                                gui[1].moveItem = None

                        elif slot.item.getRegistryName() == 'null_item':
                            stack1 = one

                        else:
                            continue

                        # Place the carried item into the clicked slot
                        gui[1].__getattribute__('inv'+str(s%2 + 1)).items['main'][s//2] = stack1
                        # game.player.inventory.items['main'][s] = stack1

                    elif slot.item.getRegistryName() != 'null_item' and slot.item.stackSize > 0:
                        stack1, stack2 = slot.item.split()
                        gui[1].__getattribute__('inv'+str(s%2 + 1)).items['main'][s//2] = stack1
                        # game.player.inventory.items['main'][s] = stack1

                        if stack2 and stack2.getRegistryName() != 'null_item':
                            gui[1].moveItem = [s, stack2]

def onInvMouseClick(game, mousePos, pressed, event):
    """
    Event Hook: onMouseClick
    Handle the movement of items between slots in the inventory screen
    """
    gui = game.getGui()
    if gui and gui[0] == game.getModInstance('ClientMod').inventoryGui:
        # moveItem needs to store the section of inventory, index of inv.itemSlots it is from, and the itemstack itself
        for s, slot in enumerate(gui[1].itemSlots):
            if slot.button.isHovered(mousePos):
                # If the player has clicked on a slot in the inventory
                if pressed[0]:
                    # LMB click
                    # If carrying an itemstack
                    if gui[1].moveItem:
                        stack1, stack2 = gui[1].moveItem[2].add(slot.item)
                        # Place the carried item into the clicked slot
                        section = 'main' if s < 16 else ['left', 'right', 'armour'][s-16]
                        if section == 'main':
                            game.player.inventory.items['main'][s] = stack1
                        else:
                            # If the player is trying to place a non-armour item in the armour slot, dont let them
                            if section == 'armour' and not isinstance(stack1.getItem(), Armour):
                                continue
                            game.player.inventory.items[section] = stack1

                        # If clicking on a filled slot, swap or add the moveItem with
                        # the stack in the slot
                        if stack2 and stack2.getRegistryName() != 'null_item':
                            gui[1].moveItem = [section, s, stack2]
                        else:
                            gui[1].moveItem = None

                    # If carrying nothing
                    else:
                        # If clicking on a filled spot, pickup the item
                        if slot.item.getRegistryName() != 'null_item':
                            section = 'main' if s < 16 else ['left', 'right', 'armour'][s-16]
                            gui[1].moveItem = [section, s, slot.item]
                            if section == 'main':
                                game.player.inventory.items['main'][s] = ItemStack(NullItem(), 0)
                            else:
                                game.player.inventory.items[section] = ItemStack(NullItem(), 0)

                elif pressed[2]:
                    # RMB click
                    # If carrying an itemstack
                    section = 'main' if s < 16 else ['left', 'right', 'armour'][s-16]
                    if gui[1].moveItem:
                        if gui[1].moveItem[2].stackSize == 1 and slot.item.getRegistryName() == 'null_item':
                            # Place the carried item into the clicked slot
                            if section == 'main':
                                game.player.inventory.items['main'][s] = gui[1].moveItem[2]
                            else:
                                # If the player is trying to place a non-armour item in the armour slot, dont let them
                                if section == 'armour' and not isinstance(stack1.getItem(), Armour):
                                    continue
                                game.player.inventory.items[section] = gui[1].moveItem[2]

                            gui[1].moveItem = None
                            continue

                        gui[1].moveItem[2], one = gui[1].moveItem[2].getOne()
                        if one == slot.item:
                            stack1, stack2 = slot.item.add(one)
                            if gui[1].moveItem[2].getRegistryName() != 'null_item':
                                stack2 = gui[1].moveItem[2].add(stack2)[0]

                            if stack2 and stack2.getRegistryName() != 'null_item':
                                gui[1].moveItem = [section, s, stack2]
                            else:
                                gui[1].moveItem = None

                        elif slot.item.getRegistryName() == 'null_item':
                            stack1 = one

                        else:
                            continue

                        # Place the carried item into the clicked slot
                        if section == 'main':
                            game.player.inventory.items['main'][s] = stack1
                        else:
                            # If the player is trying to place a non-armour item in the armour slot, dont let them
                            if section == 'armour' and not isinstance(stack1.getItem(), Armour):
                                gui[1].moveItem[2] = gui[1].moveItem[2].add(one)[0]
                                continue
                            game.player.inventory.items[section] = stack1

                    elif slot.item.getRegistryName() != 'null_item' and slot.item.stackSize > 0:
                        stack1, stack2 = slot.item.split()
                        if section == 'main':
                            game.player.inventory.items['main'][s] = stack1
                        else:
                            # If the player is trying to place a non-armour item in the armour slot, dont let them
                            if section == 'armour' and not isinstance(stack1.getItem(), Armour):
                                continue
                            game.player.inventory.items[section] = stack1

                        if stack2 and stack2.getRegistryName() != 'null_item':
                            gui[1].moveItem = [section, s, stack2]


def onGameKeyPress(game, event):
    """
    Event Hook: onKeyPress
    Handle the opening and closing of the messaging overlay
    """
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:
        chatOverlay = game.getModInstance('ClientMod').chatOverlay
        pauseOverlay = game.getModInstance('ClientMod').pauseOverlay

        # Handle keypresses if the chat overlay is open
        if not game.getGUIState().isOverlayOpen(chatOverlay):
            if game.getGUIState().isOverlayOpen(pauseOverlay):
                if event.key == pygame.K_ESCAPE:
                    game.getGUIState().closeOverlay(pauseOverlay)
                return
            elif event.key == pygame.K_ESCAPE:
                game.openOverlay(pauseOverlay, game)

            # Open global chat if the u key is pressed
            if event.key == pygame.K_u:
                game.openOverlay(chatOverlay, game)
            # Open the local chat if the t key is pressed (local will be more commonly used, realistically)
            elif event.key == pygame.K_t:
                game.openOverlay(chatOverlay, game, 'local')
            # Open the inventory
            elif event.key == pygame.K_e:
                game.openGui(game.getModInstance('ClientMod').inventoryGui, game)

        # Close the overlay if it's open
        elif event.key == pygame.K_ESCAPE:
            game.getGUIState().closeOverlay(chatOverlay)

        # Spawn a bear using a command
        if event.key == pygame.K_b:
            game.packetPipeline.sendToServer(SendCommandPacket('/spawn Bear'))

        # Spawn a horse using a command
        if event.key == pygame.K_h:
            game.packetPipeline.sendToServer(SendCommandPacket('/create Horse'))

def onInvKeyPress(game, event):
    """
    Event Hook: onKeyPress
    Handle the key press events while in the inventory screen
    """
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').inventoryGui:
        if event.key == pygame.K_ESCAPE:
            game.getGui()[1].buttons[0].onClick(game)

        # Give a sword to the player
        elif event.key == pygame.K_s:
            print('adding sword')
            resources = game.modLoader.gameRegistry.resources
            game.player.inventory.items['left'] = ItemStack(Sword(), 1)
            game.player.inventory.addItemstack(ItemStack(Dirt(), 1))

def onCommand(game, commandClass, username, args):
    """
    Event Hook: onCommand
    Extend the default behaviour for some commands
    """
    if commandClass.__name__ == 'MessageCommand':
        message = ' '.join(args[1:])
        modInstance = game.getModInstance('ClientMod')
        modInstance.chatMessages[args[0]] = modInstance.chatMessages.get(args[0], []) + [message]

        # If the message received is a P2P message, pop up the notification to the player
        if args[0] not in ['global', 'local']:
            gui = game.getGUIState()
            chatOverlay = game.getModInstance('ClientMod').chatOverlay
            if gui:
                # If we are already in the right channel, dont bother showing the notice
                if gui.isOverlayOpen(chatOverlay) and gui.getOverlay(chatOverlay).tab == args[0]:
                    return
                # Append the message to the notifications list
                gui.gui[1].notifications.append(args[0])

def onPacketReceived(game, packet):
    """
    Event Hook: onPacketReceived
    Hook additional behaviour into the vanilla API packets
    """
    if packet.__class__.__name__ == 'ResetPlayerPacket':
        # Tell the game that the player is synced
        game.player.synced = True

    elif packet.__class__.__name__ == 'InvalidLoginPacket':
        # Tell the player that their username is already taken
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)
        if game.getGui():
            game.getGui()[1].error = 'That Username Is Already Taken.'

    elif packet.__class__.__name__ == 'WorldUpdatePacket':
        # Fetch images of new players
        for p, player in enumerate(game.world.players):
            if player.img == []:
                game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPlayerImagePacket(player))

    elif packet.__class__.__name__ == 'SendInventoryPacket':
        if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').inventoryGui:
            game.getGui()[1].invSynced = True

def onDisconnect(game, message):
    """
    Event Hook: onDisconnect
    Handle the opening of the disconnected screen when the client disconnects
    """
    if message:
        gui = game.getGui()
        disconnectGuiID = game.getModInstance('ClientMod').disconnectMessageGui
        mainGuiID = game.getModInstance('ClientMod').mainMenuGui
        if message != 'Server Connection Reset' or (gui and gui[0] not in [disconnectGuiID, mainGuiID]):
            # Show the message
            game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, message)

    game.player = Player()
    # Close the connection in the packetPipeline(s)
    game.packetPipeline.closeConnection()
    game.getModInstance('ClientMod').packetPipeline.closeConnection()

def onPlayerLogin(game, player):
    """
    Event Hook: onPlayerLogin
    Run logic each time a client logs into a remote packetPipeline
    Open the player customisation screen when the client logs into the server
    """
    # Pregenerate the world
    if not game.getModInstance('ClientMod').genLock:
        queue = Queue()
        p = Process(target=genWorld, args=(game, queue))
        t = Thread(target=handleProcess, args=(game, queue))
        p.daemon = True
        t.daemon = True
        p.start()
        t.start()

        startTime = time.time()
        # Wait for the world to generate
        while not game.world.isWorldLoaded():
            # Timeout and print a message if it took too long
            if time.time()-startTime > 5:
                print('[WARNING] World took too long to generate')
                break

    # Show the player customisation screen
    game.openGui(game.getModInstance('ClientMod').playerDrawGui, game)

def onPlayerSync(game, player, oldPlayers):
    """
    Event Hook: onPlayerSync
    Apply the updates to other player attributes from the server
    """
    # If the player being updated is the client player, handle it differently
    isRiding = False
    if game.player.ridingEntity:
        vehicle = game.getVehicle(game.player.ridingEntity)
        if vehicle:
            isRiding = game.player.name in vehicle.riders['other']
        else:
            print(game.player.ridingEntity)

    if player.name == game.player.name:
        if isRiding:
            game.player.health = player.health
            game.player.pos = player.pos
        return

    for p in range(len(oldPlayers)):
        if oldPlayers[p].name == player.name:
            # Update vanilla player properties
            oldPlayers[p].health = player.health

            # Check if the player is riding on an entity
            if oldPlayers[p].ridingEntity:
                oldPlayers[p].pos = game.getVehicle(oldPlayers[p].ridingEntity).pos
            else:
                oldPlayers[p].lastPos = oldPlayers[p].pos

                # Update the modded properties
                props = oldPlayers[p].getProperty('worldUpdate')
                props.newPos = player.pos
                props.updateTick = game.tick
                oldPlayers[p].setProperty('worldUpdate', props)

            return

    prop = deepcopy(game.getModInstance('ClientMod').worldUpdateProperty)
    prop.newPos = player.pos
    player.setProperty('worldUpdate', prop)
    oldPlayers.append(player)

def onEntitySync(game, entity, entities):
    """
    Event Hook: onEntitySync
    Apply the updates to the entity from the server
    """
    # If the player being updated is the client player, skip it
    for e in range(len(entities)):
        if entities[e] == entity:
            # Update vanilla entity properties
            entities[e].health = entity.health

            # Update the modded properties
            props = entities[e].getProperty('worldUpdate')
            props.newPos = entity.pos
            props.updateTick = game.tick
            entities[e].setProperty('worldUpdate', props)

            return

    prop = deepcopy(game.getModInstance('ClientMod').worldUpdateProperty)
    prop.newPos = entity.pos
    entity.setProperty('worldUpdate', prop)
    if isinstance(entity, Pickup):
        game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPickupItem(entity.uuid))
    entities.append(entity)

def onVehicleSync(game, vehicle, vehicles):
    """
    Event Hook: onVehicleSync
    Apply the updates to the given vehicle from the server
    """
    # Iterate and update the vehicles
    for v in range(len(vehicles)):
        if vehicles[v] == vehicle:
            # Set the riders
            vehicles[v].riders = vehicle.riders
            # Update the ridingEntity values in the players
            for rider in vehicles[v].riders['other']:
                # Try to get a player
                player = game.getPlayer(rider)
                if player:
                    player.ridingEntity = vehicle.uuid
                else:
                    # If it's not a player, try to get an entity
                    entity = game.getEntity(rider)
                    if entity:
                        entity.ridingEntity = vehicle.uuid

            # Update the modded properties
            props = vehicles[v].getProperty('worldUpdate')
            props.newPos = vehicle.pos
            props.updateTick = game.tick
            vehicles[v].setProperty('worldUpdate', props)

            return

    prop = deepcopy(game.getModInstance('ClientMod').worldUpdateProperty)
    prop.newPos = vehicle.pos
    vehicle.setProperty('worldUpdate', prop)
    vehicles.append(vehicle)

def onDimensionChange(game, entity, oldDimension, newDimension):
    """
    Event Hook: onDimensionChange
    Run logic when an entity changes dimension
    """
    if isinstance(entity, Player) and entity.name == game.player.name:
        # Check if it's the client player switching dimension
        message = 'Entering '+game.getDimension(newDimension).getName()
        game.openGui(game.getModInstance('ClientMod').enteringGui, message)
