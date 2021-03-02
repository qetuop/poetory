import importlib

# 'ascendancyClass': 2, 'class': 'Trickster', 'classId': 6, 'experience': 2182014614, 'lastActive': True, 'league': 'Blight', 'level': 91, 'name': 'SalWrendMkII'


class CharacterInfo:
    def __init__(self, ascendancyClass, class_, classId, experience, lastActive, league, level, name):
        self.ascendancyClass = ascendancyClass
        self.class_ = class_   #fck this may screw up introspection...
        self.classId = classId
        self.experience = experience
        self.lastActive = lastActive
        self.league = league
        self.level = level
        self.name = name


class Item:
    def __init__(self, frameType, h, icon, id, identified, ilvl, league, name, typeLine, verified, w, x, y,
                 category=None,
                 abyssJewel=None, additionalProperties=None, artFilename=None, corrupted=None, cosmeticMods=None,
                 craftedMods=None,
                 descrText=None, duplicated=None, elder=None, enchantMods=None, explicitMods=None, flavourText=None,
                 implicitMods=None,
                 inventoryId=None, isRelic=None, lockedToCharacter=None, maxStackSize=None, nextLevelRequirements=None,
                 note=None,
                 properties=None, prophecyDiffText=None, prophecyText=None, requirements=None, secDescrText=None,
                 shaper=None,
                 socketedItems=None, sockets=None, stackSize=None, support=None, talismanTier=None, utilityMods=None,
                 fractured=None, fracturedMods=None, incubatedItem=None, veiled=None, veiledMods=None, influences=None,
                 synthesised=None):
        self.category = category
        self.frameType = frameType
        self.h = h
        self.icon = icon
        self.id = id
        self.identified = identified
        self.ilvl = ilvl
        self.league = league
        self.name = name
        self.typeLine = typeLine
        self.verified = verified
        self.w = w
        self.x = x
        self.y = y
        self.abyssJewel = abyssJewel
        self.additionalProperties = additionalProperties
        self.artFilename = artFilename
        self.corrupted = corrupted
        self.cosmeticMods = cosmeticMods
        self.craftedMods = craftedMods
        self.descrText = descrText
        self.duplicated = duplicated
        self.elder = elder
        self.enchantMods = enchantMods
        self.explicitMods = explicitMods
        self.flavourText = flavourText
        self.implicitMods = implicitMods
        self.inventoryId = inventoryId
        self.isRelic = isRelic
        self.lockedToCharacter = lockedToCharacter
        self.maxStackSize = maxStackSize
        self.nextLevelRequirements = nextLevelRequirements
        self.note = note
        self.properties = properties
        self.prophecyDiffText = prophecyDiffText
        self.prophecyText = prophecyText
        self.requirements = requirements
        self.secDescrText = secDescrText
        self.shaper = shaper
        self.socketedItems = socketedItems
        self.sockets = socketedItems
        self.stackSize = stackSize
        self.support = support
        self.talismanTier = talismanTier
        self.utilityMods = utilityMods
        self.fractured = fractured
        self.fracturedMods = fracturedMods
        self.incubatedItem = incubatedItem
        self.veiled = veiled
        self.veiledMods = veiledMods
        self.influences = influences
        self.synthesised = synthesised
        # hybrid = val gems, 2nd prop?

        #print(self.__class__, self.__module__)

# src = Adds 3 to 6 Physical Damage to Attacks, tgt = Adds # to # Physical Damage
# diff = [3,6]....at least it should
def findDiff(src,tgt):

    diff = []
    tgtSplit = tgt.split(" ")
    for y in src.split(" "):
        if y not in tgtSplit:
            diff.append(y)
    #print(f"\tFind Diff: src = {src}, tgt = {tgt}, diff = {diff}")
    return diff

def dict_to_obj(our_dict):
    """
    Function that takes in a dict and returns a custom object associated with the dict.
    This function makes use of the "__module__" and "__class__" metadata in the dictionary
    to know which object type to create.
    """
    if "__class__" in our_dict:
        # Pop ensures we remove metadata from the dict to leave only the instance arguments
        class_name = our_dict.pop("__class__")

        # Get the module name from the dict and import it
        module_name = our_dict.pop("__module__")

        # XXX We use the built in __import__ function since the module name is not yet known at runtime XXX
        module = importlib.import_module(module_name)
        # module = __import__(module_name) # dosen't work with ?nested? modules

        # Get the class from the module
        class_ = getattr(module, class_name)

        # Use dictionary unpacking to initialize the object
        obj = class_(**our_dict)
    else:
        obj = our_dict
    return obj