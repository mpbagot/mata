from api.dimension import *

class DefaultChunkProvider(ChunkProvider):
    def getName(self):
        return 'the Overworld'

    def generate(self, pos, gameRegistry):
        start = time.time()
        xPos, yPos = pos
        xPos = round(xPos)
        yPos = round(yPos)

        biomes = self.biomes
        biomeSize = self.biomeSize

        # Generate the tile noise
        # noiseMap = [[noise.snoise2(x, y, 8, 1.4, 0.45, base=gameRegistry.seed)/2+0.5 for x in range(xPos-150, xPos+151)] for y in range(yPos-105, yPos+106)]
        noiseMap = []
        for y in range(yPos - 105, yPos + 106):
            noiseMap.append([])
            for x in range(xPos - 150, xPos + 151):
                # Generate the noise value for this x,y position
                noiseMap[-1].append(noise.snoise2(x, y, 8, 1.4, 0.45, base=gameRegistry.seed)/2 + 0.5)

        # Generate the biome map noise
        # biomeNoise = [[noise.snoise2(x, y, 7, 3, 0.6-(biomeSize*0.1), base=gameRegistry.seed/2)/2+0.5 for x in range(xPos-150, xPos+151)] for y in range(yPos-105, yPos+106)]
        biomeNoise = []
        for y in range(yPos - 105, yPos + 106):
            biomeNoise.append([])
            for x in range(xPos - 150, xPos + 151):
                # Generate the noise value for this x,y position
                biomeNoise[-1].append(noise.snoise2(x, y, 7, 3, 0.6 - (biomeSize * 0.1), base=gameRegistry.seed/2)/2 + 0.5)

        # Generate the 'detail noise'. Used for plants
        # 0.85 is the threshold for trees
        # 0.7 is the threshold for plants
        # 0.5 is the threshold for grass
        detailNoise = []
        for y in range(yPos - 105, yPos + 106):
            detailNoise.append([])
            for x in range(xPos - 150, xPos + 151):
                # Generate the noise value for this x,y position
                detailNoise[-1].append((noise.snoise2(x, y, 2, 3, 0.02)**3)/2 + 0.5)

        # Generate an empty starting biome map
        width, height = (120, 84)
        biomeMap = TileMap(width, height)

        # Loop the TileMap, set biomes, then set tiles in the biome
        for y, row in enumerate(biomeMap.map):
            for x, tile in enumerate(row):
                # Set the tile in the array to be a certain biome
                biomeMap.map[y][x] = biomes[round(biomeNoise[y][x]*(len(biomes)-1))]()
                # Set the tile to be a certain type from the biome
                biomeMap.map[y][x].setTileType(noiseMap[y][x], detailNoise[y][x], gameRegistry.resources)

        print('Time taken: '+str(time.time()-start)+' seconds')

        return biomeMap
