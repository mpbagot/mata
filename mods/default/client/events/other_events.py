from threading import Thread
from multiprocessing import Process, Queue
import pygame
from copy import deepcopy
import time

import util
from api.packets import SendCommandPacket, MountPacket
from api.entity import Player
from api.vehicle import Vehicle

from mods.default.client.events.tick_events import genWorld, handleProcess

def onGameMouseClick(game, mousePos, event):
    '''
    Event Hook: onMouseClick
    Handle a mouse click on vehicles, players and entities
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:

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

def onGameKeyPress(game, event):
    '''
    Event Hook: onKeyPress
    Handle the opening and closing of the messaging overlay
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').gameGui:
        chatOverlay = game.getModInstance('ClientMod').chatOverlay
        pauseOverlay = game.getModInstance('ClientMod').pauseOverlay

        # Handle keypresses if the chat overlay is open
        if not game.getGUIState().isOverlayOpen(chatOverlay):
            if game.getGUIState().isOverlayOpen(pauseOverlay):
                if event.key == pygame.K_ESCAPE:
                    game.getGUIState().closeOverlay(pauseOverlay)
            elif event.key == pygame.K_ESCAPE:
                game.openOverlay(pauseOverlay, game)

            # Open global chat if the t key is pressed
            if event.key == pygame.K_t:
                game.openOverlay(chatOverlay, game)
            # Open the local chat if the u key is pressed
            elif event.key == pygame.K_u:
                game.openOverlay(chatOverlay, game, 'local')
            # Open the inventory
            elif event.key == pygame.K_e:
                game.openGui(game.getModInstance('ClientMod').inventoryGui, game)

        # Close the overlay if it's open
        elif event.key == pygame.K_ESCAPE:
            game.getGUIState().closeOverlay(chatOverlay)

        # Send a test message
        if event.key == pygame.K_m:
            game.packetPipeline.sendToServer(SendCommandPacket('/message global random test message'))

        # Spawn a bear using a command
        if event.key == pygame.K_b:
            game.packetPipeline.sendToServer(SendCommandPacket('/spawn Bear'))

def onInvKeyPress(game, event):
    '''
    Event Hook: onKeyPress
    Handle the key press events while in the inventory screen
    '''
    if game.getGui() and game.getGui()[0] == game.getModInstance('ClientMod').inventoryGui:
        if event.key == pygame.K_ESCAPE:
            game.restoreGui()

def onCommand(game, commandClass, username, args):
    '''
    Event Hook: onCommand
    Extend the default behaviour for some commands
    '''
    if commandClass.__name__ == 'MessageCommand':
        message = ' '.join(args[1:])
        modInstance = game.getModInstance('ClientMod')
        modInstance.chatMessages[args[0]] = modInstance.chatMessages.get(args[0], []) + [message]
        print(' '.join(args[1:]))

def onPacketReceived(game, packet):
    '''
    Event Hook: onPacketReceived
    Hook additional behaviour into the vanilla API packets
    '''
    if packet.__class__.__name__ == 'ResetPlayerPacket':
        # Tell the game that the player is synced
        game.player.synced = True

    elif packet.__class__.__name__ == 'InvalidLoginPacket':
        # Tell the player that their username is already taken
        game.openGui(game.getModInstance('ClientMod').mainMenuGui)
        game.getGui()[1].error = 'That Username Is Already Taken.'

    elif packet.__class__.__name__ == 'WorldUpdatePacket':
        # Fetch images of new players
        for p, player in enumerate(game.world.players):
            if player.img == None:
                game.getModInstance('ClientMod').packetPipeline.sendToServer(FetchPlayerImagePacket(player))

def onDisconnect(game, message):
    '''
    Event Hook: onDisconnect
    Handle the opening of the disconnected screen when the client disconnects
    '''
    if message.startswith('show_screen'):
        # Show the message
        #TODO Make this only show when I want it to
        game.openGui(game.getModInstance('ClientMod').disconnectMessageGui, message[12:])

    # Close the connection in the packetPipeline(s)
    game.packetPipeline.closeConnection()
    game.getModInstance('ClientMod').packetPipeline.closeConnection()

def onPlayerLogin(game, player):
    '''
    Event Hook: onPlayerLogin
    Run logic each time a client logs into a remote packetPipeline
    Open the player customisation screen when the client logs into the server
    '''
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
    # TODO Switch this back to the playerDrawGui once assets have been created
    game.openGui(game.getModInstance('ClientMod').gameGui, game)
    # game.openGui(game.getModInstance('ClientMod').playerDrawGui, game)

def onPlayerSync(game, player, oldPlayers):
    '''
    Event Hook: onPlayerSync
    Apply the updates to other player attributes from the server
    '''
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
                # Update the modded properties
                props = oldPlayers[p].getProperty('worldUpdate')
                props.props['newPos'] = player.pos
                props.props['updateTick'] = game.tick
                oldPlayers[p].setProperty('worldUpdate', props)

            return

    player.setProperty('worldUpdate', game.getModInstance('ClientMod').worldUpdateProperty)
    oldPlayers.append(player)

def onEntitySync(game, entity, entities):
    '''
    Event Hook: onEntitySync
    Apply the updates to the entity from the server
    '''
    # If the player being updated is the client player, skip it
    for e in range(len(entities)):
        if entities[e].uuid == entity.uuid:
            # Update vanilla entity properties
            entities[e].health = entity.health

            # Update the modded properties
            props = entities[e].getProperty('worldUpdate')
            props.props['newPos'] = entity.pos
            props.props['updateTick'] = game.tick
            entities[e].setProperty('worldUpdate', props)

            return

    entity.setProperty('worldUpdate', deepcopy(game.getModInstance('ClientMod').worldUpdateProperty))
    entities.append(entity)

def onVehicleSync(game, vehicle, vehicles):
    '''
    Event Hook: onVehicleSync
    Apply the updates to the given vehicle from the server
    '''
    # Iterate and update the vehicles
    for v in range(len(vehicles)):
        if vehicles[v].uuid == vehicle.uuid:
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
            props.props['newPos'] = vehicle.pos
            props.props['updateTick'] = game.tick
            vehicles[v].setProperty('worldUpdate', props)

            return

    vehicle.setProperty('worldUpdate', deepcopy(game.getModInstance('ClientMod').worldUpdateProperty))
    vehicles.append(vehicle)

def onDimensionChange(game, entity, oldDimension, newDimension):
    '''
    Event Hook: onDimensionChange
    Run logic when an entity changes dimension
    '''
    if isinstance(entity, Player) and entity.name == game.player.name:
        # Check if it's the client player switching dimension
        message = 'Entering '+game.getDimension(newDimension).getName()
        game.openGui(game.getModInstance('ClientMod').enteringGui, message)
