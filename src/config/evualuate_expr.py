EMOTION_REFERENCE_PROMPT = """Imagine yourself standing at the edge of a serene lake, 
surrounded by the gentle rustling of trees and the soft warmth of golden sunlight. 
The air is filled with the sweet scent of blooming flowers as far as the eye can see. 
In the distance, a faint mist rises from the water's surface, carrying the whispers 
of past triumphs. The sound of gentle lapping waves against the shore creates a soothing 
melody that calms the mind and heart. As you walk along the lake's edge, the soft grass 
beneath your feet and the warmth of the sun on your skin evoke feelings of comfort and 
gratitude for life's simple pleasures. A delicate wooden boat glides across the water, 
its gentle rocking motion echoing the rhythm of your heartbeat. In this peaceful sanctuary, 
the weight of disappointment slowly lifts, replaced by a sense of nostalgia and appreciation 
for the beauty that surrounds you."""

EMOTION_REFERENCE_PROMPT_REASON = """scores 1 because despite having some warm and pleasant 
visual elements (golden sunlight, blooming flowers, a wooden boat on a lake), 
none of them are specifically chosen to evoke the target emotion. 
The description is entirely interchangeable — the same world could be used for Joy, 
Nostalgia, Peace, or Sadness with minimal changes. 
There is no visual element that directly anchors to the target emotion, 
no contrast or tension that suggests an emotional direction, 
and no symbolic charge that points toward a specific feeling. 
It is pleasant but emotionally inert."""

CARDINAL_REFERENCE_PROMPT_1 = """Imagine a sunlit savannah at dawn, where golden grasses 
sway gently in the morning breeze. A subtle mist rises from the earth, carrying the scent 
of blooming wildflowers. In this serene landscape, a majestic tree stands tall, its branches 
adorned with vibrant yellow and orange streamers, symbolizing the joy and warmth of connection. 
As you wander through this idyllic world, the soft rustling of leaves and the distant songs of 
birds create a soothing melody, evoking feelings of gratitude and peaceful coexistence. Amidst 
the lush greenery, a winding path invites exploration, leading to hidden clearings and secret 
glades, where the gentle warmth of sunlight nurtures the soul. The atmosphere is filled with 
an air of hope and renewal, as if the very presence of loved ones has awakened the beauty within."""

CARDINAL_REFERENCE_PROMPT_1_REASON = """scores 1 because the world lands entirely at the 
destination pole — warmth, connection, gratitude — with no trace of the source state (loss, 
absence, grief). There is no before: nothing in the landscape has been dark, empty, or severed. 
The mist, the streamers, the birdsong all arrive already joyful, so the reader cannot feel any 
movement from one emotional state toward another. The final line ('as if the very presence of 
loved ones has awakened the beauty within') gestures at a transformation, but because nothing 
in the world was ever absent or wounded, there is nothing to awaken from. A faint directional 
trace earns it a 1 rather than a 0, but the transition is never enacted."""

CARDINAL_REFERENCE_PROMPT_2 = """As the floodlights dimly illuminate the empty football pitch,
the echoes of past glories linger in the air. The once-vibrant crowd is now replaced by a sea
of nostalgia, where memories of Italy's triumphant moments are relived. The blue jerseys of the
Italian team, now faded and worn, serve as a poignant reminder of what could have been. Amidst
this melancholic landscape, the faint glow of hope begins to emerge, like the first light of
dawn breaking through the clouds. The stadium's empty corridors whisper tales of past victories,
while the sound of distant cheering grows louder, beckoning the user toward a brighter future."""

CARDINAL_REFERENCE_PROMPT_2_REASON = """scores 2 because both poles are nominally present —
the desolation and faded jerseys suggest the source state (disappointment, loss), and the
'faint glow of hope' names the destination — but the world never actually moves between them.
The two poles coexist as static labels rather than enacting a journey: the source is described,
the destination is announced, but no visual element changes or transforms during the description.
You can identify a before and an after intellectually, but you never feel the crossing."""