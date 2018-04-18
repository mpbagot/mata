import random
from copy import deepcopy
import time

from api.item import *
from api.packets import *

from mods.default.items import *
from mods.default.packets import *

def onTickUpdateTradeRequests(game, deltaTime, tick):
    '''
    Event Hook: onTick
    Remove expired trade requests
    '''
    for dimensionId in self.modLoader.gameRegistry.dimensions:
        for p, player in enumerate(game.getWorld(dimensionId).players):
            props = player.getProperty('tradeState')
            # Loop the requests
            for item in list(props.requests.items()):
                # If a request has existed for more than a minute, remove it
                if time.time()-item[1] >= 60:
                    props.requests.pop(item[0])
            game.getWorld(dimensionId).players[p].setProperty('tradeState', props)

def onTick(game, deltaTime, tick):
    '''
    Event Hook: onTick
    Send out WorldUpdatePackets to players
    '''
    if tick%(util.FPS//6) == 0:
        # Send server updates to all of the connected clients 6 times a second
        pp = game.packetPipeline
        connections = pp.connections.keys()
        # Loop the keys
        for c in list(connections):
            # Get the connection object from the dictionary
            conn = pp.connections.get(c)
            # If it has been deleted by the other thread during iteration, skip it
            if not conn:
                continue
            # If the player has logged in, send the world update data to them
            if conn.username:
                player = game.getPlayer(conn.username)
                # Customise the packet for each player
                packet = WorldUpdatePacket(game.getWorld(player.dimension), player)
                pp.sendToPlayer(packet, conn.username)

def onPlayerMount(game, player, entity, success, mode):
    '''
    Event Hook: onPlayerMount
    Sync the new player position to the client when the player mounts an entity
    '''
    # If the player is mounting an entity (as opposed to dismounting)
    if success and mode == 'mount':
        # Set the player position
        player.setPos(entity.pos)

        # Create and send the sync packet
        packet = ResetPlayerPacket(player)
        game.packetPipeline.sendToPlayer(packet, player.name)

def onPlayerDeath(game, player, tickDamage):
    '''
    Event Hook: onPlayerDeath
    Close the connection to the client and drop the player's inventory
    '''
    # Drop the player's inventory on the ground
    world = game.getWorld(player.dimension)
    # Turn the itemstacks into Pickups and spawn them in the world
    items = player.inventory.toList()
    pieceEntities = [a.toPickup(game, player.pos) for a in items]
    for p, piece in enumerate(pieceEntities):
        world.spawnEntityInWorld(piece)

    if tickDamage and isinstance(tickDamage.source, str):
        # Give experience points = enemy lvl**0.75 + 5. (lvl = exp**0.5)
        xpToGive = int((player.exp**0.5+1)**(3/4)+5)
        playerToGive = game.getPlayer(tickDamage.source)
        if playerToGive:
            playerToGive.exp += xpToGive
            game.packetPipeline.sendToPlayer(ResetPlayerPacket(playerToGive, bits=8), playerToGive.name)

    # Close the connection to the client from the server
    pp = game.packetPipeline
    pp.sendToPlayer(DisconnectPacket('You have died'), player.name)
    game.fireEvent('onDisconnect', player.name)
    game.fireCommand('System', '/message global Player {} has died.'.format(player.name))

def onEntityDeath(game, entity, tickDamage):
    '''
    Event Hook: onEntityDeath
    Drop gold and items
    '''
    if isinstance(entity, Pickup):
        return

    if tickDamage and isinstance(tickDamage.source, str):
        # Give experience points = 1.5 * 4**(entity.hp/player.hp)
        playerToGive = game.getPlayer(tickDamage.source)
        if playerToGive:
            xpToGive = int(1.5 * 4**(entity.health/playerToGive.health) + entity.health//20)
            playerToGive.exp += xpToGive

    world = game.getWorld(entity.dimension)
    resources = game.modLoader.gameRegistry.resources
    goldAmount = random.randint(1, int(sum([abs(a) for a in entity.pos])**0.5)+1)

    # Split the gold into several pieces
    pieces = []
    while goldAmount > 50:
        pieces.append(ItemStack(Gold(), 50))
        goldAmount -= 50
    pieces.append(ItemStack(Gold(), goldAmount))

    # Turn the itemstacks into Pickups and spawn them in the world
    pieceEntities = [a.toPickup(game, entity.pos) for a in pieces]
    for p, piece in enumerate(pieceEntities):
        world.spawnEntityInWorld(piece)

    print('Entity died')

def onEntityDamage(game, entity, damage):
    '''
    Event Hook: onEntityDamage & onPlayerDamage
    Subtract health from the entity according to the damage class
    '''
    entity.health -= damage.amount
    if entity.health <= 0:
        entity.isDead = True

    if isinstance(entity, Player):
        game.packetPipeline.sendToPlayer(ResetPlayerPacket(entity, bits=3), entity.name)

def onPlayerLogin(game, player):
    '''
    Event Hook: onPlayerLogin
    Print a little message when a player connects
    '''
    print(player.name + ' joined the server.')

    # Sync the inventory to the player
    pp = game.getModInstance('ServerMod').packetPipeline
    pp.sendToPlayer(SendInventoryPacket(player.inventory), player.name)

def onPlayerCreated(game, player):
    '''
    Event Hook: onPlayerCreated
    Give some basic items to new players
    '''
    # Add a steel sword
    player.inventory.items['left'] = ItemStack(Sword(), 1)

    # Give the player a tradestate to handle trading
    props = deepcopy(game.getModInstance('ServerMod').tradeStateProperty)
    player.setProperty('tradeState', props)

def onDisconnect(game, username):
    '''
    Event Hook: onDisconnect
    Print a little message in the server console
    '''
    print('Client player "' + username + '" has disconnected')

    player = game.getPlayer(username)
    # Unmount the player
    if player and player.ridingEntity:
        vehicle = game.getVehicle(player.ridingEntity)
        if vehicle:
            vehicle.unmountRider(player)
        player.ridingEntity = None
    # TODO Move the player out of danger. Somehow...

    game.packetPipeline.closeConnection(username)
    game.getModInstance('ServerMod').packetPipeline.closeConnection(username)
