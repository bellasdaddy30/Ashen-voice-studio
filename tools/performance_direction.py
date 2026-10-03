"""Hand direction for every chapter's dialogue: {chapter: "index:tag,tag index:tag ..."}.
Index = the line's position among that chapter's dialogue lines (see list_dialogue.py).
A listed index REPLACES the automatic tags for that line; "-" clears them.
Unlisted lines keep the automatic tags from the prose cues."""
DIRECTION = {
1: """0:warmly 1:dryly 2:dryly 3:dryly 4:deadpan 5:dryly 6:teasing 7:dryly 8:amused 11:playfully
12:eager 13:deadpan 14:defensive 15:dryly 16:amused 18:disappointed 20:knowingly 22:puzzled 24:surprised 25:satisfied
26:curious 29:intrigued 30:darkly 31:curious 33:eagerly 35:impatient 36:amused 38:dryly 39:deadpan
41:curious 43:skeptical 49:impressed 50:dryly 51:amused 53:groans 55:whining 57:thoughtful 59:quietly
64:eager 66:sheepish 67:curious 68:thoughtful 69:quietly 70:quietly 71:ominous 72:ominous 73:firmly
75:whispers,teasing 76:seriously 77:dryly 78:dryly 79:quietly 81:dryly 82:dryly 83:uneasy 84:quietly
86:suspicious 87:eager 88:sharply 89:firmly 90:sharply 91:innocently 92:firmly 94:tense
97:whispers,warning 101:solemn 102:solemn""",
2: """1:uneasy 2:gruffly 3:quietly 4:softly 5:grumbling 6:dryly 7:dryly 8:gently 10:softly 11:quietly 12:wistful 13:wistful
15:gently 16:flatly 17:gently 19:softly 20:quietly 21:gruffly 23:knowingly 24:coldly 26:quietly 28:coldly 29:bitterly
32:grimly 33:dismissively 34:dryly 35:quietly 36:firmly 37:approvingly 38:knowingly""",
3: """4:teasing 5:dryly 6:amused 7:dryly 9:dryly 10:satisfied 11:dryly 12:mock-offended 13:amused 14:dryly 15:fondly
16:indignant 17:teasing 18:primly 19:teasing 21:grumbling 22:smugly 23:softly 24:quietly 25:thoughtful 28:knowingly
29:thoughtful 38:meaningfully 39:thoughtful 40:skeptical 41:quietly 43:dryly 44:darkly 45:puzzled 46:flatly 48:tired 50:wearily""",
4: """0:approvingly 2:curious 3:quietly 7:quietly 8:dryly 11:firmly 12:skeptical 15:softly 16:thoughtful 17:quietly 19:quietly
20:wistful 21:fondly 22:teasing 25:proudly 27:fondly 28:amused 29:dryly 30:softly 31:grumbling 32:teasing 33:dryly 34:quietly
38:curious 39:firmly 40:knowingly 41:quietly""",
5: """0:dryly 1:dryly 2:smoothly 3:skeptical 4:smoothly 5:pointedly 6:coldly 7:flatly 10:sarcastic 11:flatly 12:insinuating
13:coldly 14:skeptical 15:flatly 16:smoothly 17:coldly 18:dismissively 19:annoyed 20:smoothly 21:sarcastic 22:dryly 24:dryly
25:knowingly 26:evasive 32:amused 33:impatient 34:smoothly 35:sharply 36:smoothly 37:dryly 38:pleased 40:dryly 44:amused 45:dryly
48:guarded 49:smoothly 50:teasing 51:dryly 53:dryly 54:amused 55:shyly 56:surprised 57:shyly 58:shyly 59:slowly 61:skeptical
63:wistful 64:wistful 66:fondly 68:amused 69:fondly 70:curious 71:amused 72:gruffly 74:curious 75:dryly 76:quietly 77:flatly
78:sadly 79:shyly 80:wistful 81:quietly 82:gravely 83:gravely 84:firmly 85:fondly 86:dryly 87:amused 88:gently 89:quietly
90:teasing 91:surprised 92:teasing 93:dryly 94:uneasy 95:quietly 96:dismissively 97:skeptical 98:dismissively 99:quietly
100:sharply 101:dryly 102:suspicious 103:knowingly 105:gently 106:knowingly 107:evasive 108:sharply 109:dryly 110:sadly
111:dryly 112:quietly 113:dryly 114:softly 117:softly 118:wistful 119:quietly 121:coughs,softly 122:thoughtful 123:solemn 124:solemn""",
6: """0:knowingly 1:flatly 2:dryly 3:intense 4:suspicious 6:curious 7:flatly 8:skeptical 9:intense 10:guarded 12:sharply 13:evasive
14:impatient 15:surprised 17:alarmed 18:dryly 19:skeptical 20:dryly 21:curious 27:testing 28:slowly 29:intrigued 30:testing
32:intrigued 33:approvingly 36:slowly 37:realizing 38:quietly 39:satisfied 40:grumbling 41:curious 43:firmly 49:quietly
50:skeptical 52:thoughtful 53:pointedly 54:quietly 55:firmly 56:skeptical 57:intense 59:dryly 60:firmly 61:dryly 62:puzzled
64:stunned 65:calmly 66:quietly 67:calmly 68:sharply 69:sharply 70:calmly 71:defensive 72:slowly 73:coldly 74:suspicious
75:guarded 76:knowingly 77:flatly 78:firmly 79:intense 82:firmly 83:shrewdly 84:flatly 85:skeptical 87:intense 88:coldly
89:calmly 90:coldly 91:dryly 92:impatient 93:firmly 94:softly""",
7: """0:gravely 1:gravely 2:ominous 3:warning 4:sorrowful 5:sorrowful 6:flatly 7:quietly 8:quietly 9:quietly 10:quietly 11:quietly
12:bitterly 13:bitterly 14:dryly 15:whispers 16:uneasy 17:thoughtful 18:dryly 20:quietly 21:testing 22:dryly 23:curious
25:knowingly 26:pointedly 27:dismissively 28:dryly 29:pointedly 30:dryly 31:intense 32:pointedly 33:skeptical 34:sharply
35:curious 37:solemn 38:alarmed 39:calmly 40:uneasy 41:pointedly 42:quietly 43:sharply 45:tense 46:dryly 47:uneasy 48:dryly
49:grumbling 50:quietly 51:darkly 52:tense 53:quietly 54:alarmed 55:tense 57:tense 58:tired 59:softly 60:quietly 61:intense
62:intense 63:firmly 64:tense 65:firmly 66:quietly 67:dryly 68:firmly 69:tense 70:urgently 71:uneasy 72:desperate 73:firmly
74:desperate 75:tense 76:sharply 77:firmly 78:pleading 79:firmly 80:desperate 81:quietly 82:grimly 83:knowingly 84:suspicious
85:quietly 86:ominous 87:firmly""",
8: """0:uneasy 1:dryly 2:teasing 3:primly 4:teasing 5:firmly 6:thoughtful 7:firmly 8:dryly 9:firmly 10:curious 11:dryly
12:grumbling 13:dryly 14:tense 15:knowingly 16:quietly 17:curious 20:thoughtful 21:uneasy 22:dryly 23:sarcastic 24:sarcastic
25:dryly 26:grumbling 27:curious 28:dryly 29:quietly 30:wryly 31:dryly 33:approvingly 34:dryly 35:teasing 36:flatly 37:dryly
38:alert 39:confidently 40:thoughtful 41:curious 42:skeptical 43:thoughtful 44:uneasy 45:uneasy 46:dryly 47:grumbling
48:thoughtful 51:curious 52:ominous 53:whispers,tense 54:sharply 55:evasive 56:dryly 57:firmly 58:flatly 59:sarcastic
60:quietly 61:dismissively 62:skeptical 63:dryly 64:dryly 65:firmly 66:sarcastic 67:dryly 68:sarcastic 69:dryly 70:skeptical
71:dryly 72:indignant 73:dryly 74:tense 76:knowingly 77:thoughtful 79:frustrated 80:dryly 81:intense 82:uneasy 83:intently
84:curious 85:intently 88:knowingly 89:curious 92:shrewdly 93:cautiously 94:sighs 95:quietly 96:quietly 97:ominous 98:uneasy
99:tense 100:evasive 101:skeptical 102:quietly 103:urgently 104:stubbornly 105:urgently 106:stubbornly 107:impatiently
108:quietly 109:quietly 110:tense 111:whispers 112:urgently 113:urgently 114:alarmed 115:firmly 116:insistent 117:stunned
118:quietly 119:ominous 120:shouts 121:urgently 122:breathless 123:dryly 124:breathless 125:tense 126:dryly 127:dryly
128:teasing 129:dryly 130:dryly 131:uneasy 132:quietly 133:grimly""",
9: """0:indignant 1:sarcastic 2:defensive 3:sarcastic 4:uneasy 5:dryly 6:grumbling 7:dryly 8:grumbling 9:quietly 10:quietly
11:uneasy 12:quietly 13:curious 14:uneasy 15:whispers,firmly 16:curious 17:whispers 18:quietly 19:cautiously 20:quietly
22:intently 23:intently 24:curious 25:quietly 27:firmly 28:firmly 29:curious 30:quietly 31:curious 32:shaken 33:skeptical
34:quietly 35:uneasy 36:quietly 37:sharply 38:evasive 39:sharply 40:quietly 41:intently 42:quietly 43:uneasy 44:quietly
45:uneasy 46:quietly 47:uneasy 48:thoughtful 49:curious 50:knowingly 51:grimly 52:grimly 53:thoughtful 54:pointedly
55:uneasy 56:ominous 57:uneasy 58:breathless 60:sharply 62:urgently 63:dazed 64:gently 65:dazed 66:gently 67:gently 68:dazed
69:panicked 71:sharply 72:desperate 73:desperate 74:firmly 75:desperate 76:firmly 77:desperate 79:defiantly 80:uneasy
81:triumphant 82:grimly 88:urgently 89:urgently 90:desperate 92:shouts 93:urgently 94:strained 95:shouts 96:indignant
97:sarcastic 98:indignant 99:sarcastic 101:firmly 103:dryly 104:quietly 105:flatly 106:firmly 107:curious 108:bitterly
109:firmly 111:dryly""",
10: """0:annoyed 1:uneasy 2:thoughtful 3:firmly 4:grumbling 5:dryly 6:uneasy 9:sharply 10:suspicious 11:firmly 12:skeptical
13:curious 14:quietly 15:curious 16:softly 17:softly 18:skeptical 19:firmly 20:skeptical 21:defensive 22:dryly 23:firmly
24:uneasy 25:quietly 26:sharply 27:gently 28:uneasy 29:quietly 30:uneasy 31:ominous 32:uneasy 33:whispers,tense 34:quietly
35:sarcastic 36:thoughtful 37:quietly 38:impatient 39:firmly 40:surprised 41:grimly 42:dryly 43:quietly 44:curious 45:firmly
46:curious 47:evasive 48:pointedly 49:defensive 50:dryly 51:sharply 52:thoughtful 53:quietly 55:intently 56:intently
57:skeptical 58:dryly 59:tense 60:curious 61:alarmed 62:ominous 63:uneasy 64:quietly 65:pointedly 66:defensive 67:sharply
68:dismissively 69:grimly 70:curious 71:flatly 72:curious 73:quietly 74:curious 75:bitterly 76:quietly 77:ominous
78:shouts,grumbling 79:wary 80:calmly 81:skeptical 82:calmly 83:defiantly""",
11: """0:tense 1:intently 2:annoyed 3:firmly 5:firmly 6:nervous 7:nervous 8:gruffly 9:sullen 10:patiently 11:sullen 12:patiently
13:sullen 15:dryly 16:eager 17:surprised 18:matter-of-fact 19:casually 20:quietly 21:thoughtful 22:unsure 23:unsure 24:curious
25:frustrated 26:curious 27:frustrated 28:curious 29:frustrated 30:frustrated 31:uneasy 32:uneasy 33:tense 34:uneasy 35:sharply
36:nervous 37:suspicious 38:nervous 39:sharply 40:nervous 41:hesitant 43:hesitant 44:ominous 46:intently 47:curious
48:thoughtful 49:uneasy 51:firmly 52:ominous 53:intently 54:impatient 55:intently 56:uneasy 57:impatient 58:uneasy
59:grumbling 60:intense 61:uneasy 62:dismissively 63:firmly 64:uneasy 65:quietly 66:hesitant 68:shrewdly 69:dryly 70:grimly""",
12: """0:grimly 1:flatly 2:flatly 3:grimly 4:uneasy 5:quietly 6:tense 7:thoughtful 8:quietly 9:uneasy 10:uneasy 11:quietly
12:ominous 13:curious 14:quietly 15:intently 16:curious 17:quietly 18:softly 19:thoughtful 20:quietly 21:grimly 22:grimly
23:gruffly 24:softly 25:gently 26:sadly 27:gently 28:quietly 29:gently 30:quietly 31:softly 32:gently 33:softly
35:flatly 37:determined 38:quietly""",
13: """0:tense 1:firmly 2:defiantly 3:firmly 4:quietly 5:firmly 6:quietly 7:firmly 8:quietly 9:pleading 10:intense 11:firmly
12:defiantly 15:firmly 16:urgently 17:intense 18:angrily 19:impatient 20:firmly 21:firmly 22:firmly 23:approvingly 24:dryly
25:dryly 27:quietly 28:skeptical 29:firmly 30:precisely 31:satisfied 33:primly 34:amused 35:dryly 36:uneasy 37:grimly""",
14: """0:smoothly 1:guarded 2:smoothly 3:smoothly 4:gruffly 6:shrewdly 7:smoothly 8:gravely 9:quietly 10:gravely 11:smoothly
12:defiantly 13:coldly 14:softly 15:dryly 17:thoughtful 18:shrewdly 19:intense 20:firmly 21:firmly 22:curious 23:thoughtful
24:curious 26:thoughtful 27:skeptical 28:intrigued 29:curious 30:quietly 31:intrigued 32:skeptical 33:dryly 34:amused 35:urgently
36:whispers,excited 37:skeptical 38:quietly 39:breathless 40:intently 41:puzzled 42:intently 43:intently 44:quietly 46:quietly
48:quietly 49:quietly 50:curious 51:intently 52:quietly 53:uneasy 54:grumbling 55:flatly 57:uneasy 58:grimly 59:grimly 60:intense""",
15: """0:grumbling 1:dryly 2:shrewdly 3:quietly 4:quietly 5:dryly 6:flatly 8:firmly 9:sharply 10:intense 11:intrigued 12:intense
13:intense 14:curious 15:firmly 16:firmly 17:decisively 18:firmly 19:whispers,skeptical 20:whispers 21:whispers,skeptical
22:whispers 23:whispers,dryly 24:whispers,dryly 25:whispers 26:whispers 27:whispers 28:whispers 29:whispers,impatient
30:whispers,surprised 31:whispers,dryly 32:whispers,disapproving 33:whispers,primly 34:whispers,dryly 35:whispers,dryly
36:whispers 37:whispers,dryly 38:whispers 39:whispers,dryly 40:whispers,dryly 41:whispers,curious 42:whispers,evasive
43:whispers,dryly 44:whispers,dryly 45:whispers 46:whispers 47:whispers 48:whispers,dryly 49:whispers 50:whispers 51:whispers
52:whispers 53:whispers 54:whispers,amused 55:whispers,dryly 56:whispers,dryly 57:whispers,knowingly 58:whispers 59:whispers,dryly
60:whispers,dryly 61:whispers,uneasy 62:whispers,impatient 63:whispers 64:whispers,excited 65:whispers,tense 66:whispers
67:whispers 68:whispers 69:whispers,bitterly 70:whispers,dryly 71:whispers,bitterly 72:whispers,urgently 73:whispers,stunned
74:whispers 75:whispers 76:whispers 77:whispers 78:whispers,slowly 79:whispers 80:whispers 81:whispers 82:whispers
83:whispers,slowly 84:whispers,tense 85:whispers 86:whispers,impatient 87:whispers,frustrated 88:whispers 89:whispers
90:whispers 91:whispers 92:whispers,uneasy""",
16: """0:calmly 1:dryly 2:dryly 3:whispers,sharply 4:dryly 5:dryly 6:quietly 7:tense 8:quietly 9:intense 10:dryly 11:dryly 12:sharply
13:bitterly 14:intense 15:quietly 16:horrified 17:whispers,angrily 18:calmly 19:quietly 20:urgently 21:quietly 22:gravely
23:whispers 24:quietly 25:gravely 27:whispers 28:whispers,dryly 29:whispers 30:whispers,dryly 31:whispers,tense 32:whispers
33:whispers,dryly 34:whispers,dryly 35:shouts,impatient 36:quietly 37:intense 38:quietly 39:urgently 40:sadly 41:urgently
42:quietly 43:urgently 44:gravely 45:whispers,intense 46:gravely 47:stunned 48:quietly 50:quietly 51:gravely 52:urgently
53:gravely 55:quietly 56:shouts,impatient 57:shouts,calmly 58:suspicious 59:shouts,calmly 60:suspicious 61:shouts,dryly
62:whispers,urgently 63:whispers,urgently 64:whispers 65:whispers,dryly 66:whispers 67:whispers 68:whispers 69:whispers,tense
70:whispers,dryly 71:whispers 72:whispers 73:whispers 74:whispers 75:whispers,impatient 76:whispers,dryly 77:whispers,impatient
78:whispers,flatly 79:whispers,disgusted 80:dryly 81:whispers,dryly 82:suspicious 83:suspicious 84:calmly 85:gravely
86:gravely 87:shouts,angrily 88:calmly 89:whispers,urgently 90:whispers,firmly 91:whispers,desperate 92:whispers,firmly
93:whispers,pleading 94:whispers,urgently 95:whispers,stubbornly 96:whispers,firmly 97:whispers,stubbornly 98:whispers,urgently
100:whispers,firmly 101:whispers,flatly 102:whispers,dryly 103:whispers,primly 104:shouts,angrily 105:urgently 106:urgently,shouts
108:whispers 109:whispers 110:whispers,firmly 111:whispers 112:whispers,uneasy 113:whispers,dryly 114:whispers,grumbling
115:whispers,urgently 117:whispers,intently 118:whispers,dryly 119:whispers,intently 120:whispers,intently 121:whispers
122:whispers,uneasy 123:whispers,alarmed 124:whispers,dryly 125:urgently 126:urgently 127:urgently 128:urgently 129:tense
130:tense 131:tense 132:ominous 133:incredulous 134:firmly 135:incredulous 136:firmly 137:grumbling 138:quietly 139:curious
140:solemn 141:uneasy 142:solemn 143:sharply 144:tense 145:skeptical 146:tense 147:sharply 148:alarmed 149:defensive
150:dryly 151:urgently 152:urgently 153:breathless 154:urgently 155:breathless 156:urgently 157:urgently 158:strained
159:whispers,firmly 160:whispers 161:whispers,calmly 162:whispers,dryly 163:whispers,dryly 164:uneasy""",
17: """0:sharply 1:dryly 2:primly 3:dryly 4:primly 5:impatient 6:impatient 7:quietly 8:sarcastic 9:dryly 10:intently 11:skeptical
12:firmly 13:intently 15:intently 16:uneasy 17:dryly 18:grumbling 19:dryly 20:whispers,awed 21:dryly 22:intently 23:dismissively
25:surprised 26:thoughtful 27:thoughtful 28:thoughtful 29:thoughtful 30:thoughtful 31:frustrated 32:dryly 33:firmly 34:intently
35:impatient 36:quietly 37:realizing 38:excited 39:intently 40:curious 41:quietly 42:skeptical 43:intently 44:uneasy 46:uneasy
47:ominous 48:intently 49:curious 50:intently 51:curious 52:quietly 53:intently 55:intently 56:quietly,shaken 57:quietly
58:quietly 59:uneasy 60:uneasy 61:quietly 62:uneasy 63:quietly 64:horrified 65:quietly 67:dryly 68:gruffly 69:shaken
70:grimly 71:quietly 72:uneasy 73:whispers 74:quietly 75:ominous 76:tense 77:quietly 78:stunned 79:quietly 80:quietly
81:gently 82:whispers 83:uneasy 84:solemn,sorrowful 85:grimly 86:quietly 87:quietly""",
18: """0:solemn 1:firmly 2:practical 3:briskly 4:shrewdly 5:quietly 6:gruffly 8:coldly 9:nervous 10:coldly 11:nervous 12:dryly
13:nervous 14:dismissively 15:nervous 16:dryly 17:nervous 18:dryly 19:nervous 20:nervous 21:sharply 22:coldly 23:nervous
24:coldly 25:nervous 26:intense 27:nervous 28:nervous 29:coldly 30:nervous 31:sharply 32:intense 33:nervous 34:coldly
35:nervous 36:dismissively 37:calmly 38:ominous 39:ominous 40:solemn""",
19: """0:gruffly 1:flatly 2:sharply 3:flatly 4:dryly 5:quietly 6:curious 7:flatly 8:alarmed 9:grimly 10:intently 11:flatly
12:knowingly 13:dryly 14:dryly 15:dryly 16:curious 17:quietly 18:dryly 19:uneasy 20:intently 21:flatly 22:intently 23:dryly
24:firmly 25:dryly 26:dryly 27:dryly 28:tense 29:flatly 30:suspicious 31:dryly 32:dryly 33:firmly 34:skeptical 35:firmly
36:skeptical 37:dryly 38:skeptical 39:dryly 40:briskly 41:incredulous 42:primly 43:pointedly 44:primly 45:pointedly 46:primly
47:sarcastic 48:primly 49:skeptical 50:flatly 51:pointedly 52:firmly 53:curious 54:darkly 55:uneasy 56:dryly 57:uneasy
58:dismissively 59:uneasy 60:ominous 61:defiantly 62:pointedly 63:quietly 64:angrily 65:defensive 66:sarcastic 67:alarmed
68:tense 69:exasperated 70:exasperated 71:alarmed 72:uneasy 73:tense 74:alarmed 75:sarcastic 76:sarcastic 77:skeptical
78:grimly 79:incredulous 80:grimly 81:primly 82:grimly 83:firmly 84:stubbornly 85:urgently 86:stubbornly 87:urgently 88:urgently
89:urgently 90:breathless 91:urgently 92:breathless 93:shouts,angrily 94:hurriedly 95:shouts,suspicious 96:dryly 97:uneasy
98:curious 99:uneasy 100:dryly 101:tense 102:firmly 103:pointedly 104:dryly 105:dryly 106:dryly 107:whispers 108:whispers
109:whispers,tense 110:whispers 111:whispers,dryly 112:whispers 113:whispers 114:whispers,impressed 115:whispers,dryly
116:whispers,annoyed 117:whispers,dryly 118:whispers,annoyed 119:whispers,dryly 120:whispers 121:whispers 122:whispers,intently
123:whispers,intently 124:whispers,uneasy 125:whispers 126:whispers 127:whispers,uneasy 128:whispers,grimly 129:whispers,dryly
130:whispers,indignant 131:whispers,gruffly 132:whispers,stubbornly 133:whispers,dryly 134:whispers,primly 135:whispers,dryly
136:whispers,primly 137:whispers,curious 138:whispers 139:whispers,skeptical 140:whispers,dryly 141:solemn 142:whispers,intently
143:whispers 144:whispers 145:whispers,uneasy 146:whispers,intently 147:whispers 148:whispers 149:whispers,realizing
150:warning 151:sorrowful 152:whispers,angrily 153:whispers,defensive 154:whispers,angrily 155:whispers,defensive
156:whispers,bitterly 157:whispers,quietly 158:whispers,flatly 159:whispers,firmly 160:whispers 161:whispers,softly 162:softly""",
20: """0:softly 1:quietly,dryly 2:smoothly 3:smoothly 4:quietly 5:amused 6:quietly,tense 7:smoothly 8:quietly,sharply 9:smoothly 10:softly 11:quietly 12:dryly 13:quietly,accusing 14:smoothly 15:quietly,intense 16:softly 17:quietly,tense 18:slowly 19:quietly,defensive 20:smoothly 21:quietly,angrily 22:smoothly 23:quietly,sharply 24:smoothly 25:quietly,sarcastic 26:smoothly 27:whispers,intently 28:quietly 29:whispers,intently 30:smoothly 31:quietly,intense 32:softly 33:quietly 34:softly 35:quietly,confused 36:smoothly 37:quietly,stunned 38:softly 39:quietly 40:gravely 41:whispers 43:quietly,shaken 44:gently 45:quietly,bitterly 46:gently 47:quietly,bitterly 48:gently 49:quietly,bitterly 50:softly 51:quietly,bitterly 52:smoothly 53:quietly 54:smoothly 56:smoothly 57:whispers,intently 58:dryly 59:whispers,indignant 60:dryly 61:whispers,urgently 62:whispers,sharply 63:whispers,stubbornly 64:whispers,dryly 67:softly 68:quietly 69:smoothly 70:quietly,realizing 71:quietly,intense 72:quietly,intense 73:smoothly 74:quietly,sharply 75:smoothly 76:quietly,sharply 77:quietly,realizing 78:smoothly 79:quietly,pointedly 80:smoothly 81:quietly 82:smoothly 83:quietly,flatly 84:amused 86:quietly 87:quietly 88:smoothly 89:quietly,accusing 90:smoothly 91:quietly,sharply 92:smoothly 93:quietly,tense 94:softly 95:softly 96:softly 97:ominous 98:quietly,realizing 99:softly 100:quietly,uneasy 101:smoothly 102:quietly 103:smoothly 104:quietly 105:smoothly 106:quietly 107:smoothly 108:quietly,uneasy 109:dryly 110:whispers,sharply 111:whispers,defensive 112:whispers,sharply 113:whispers,dryly 114:whispers,dryly 115:whispers,coldly 116:amused 117:whispers 118:amused 119:whispers,flatly 120:whispers,dryly 121:quietly,tense 122:smoothly 123:quietly,sharply 124:softly 125:quietly,defensive 126:smoothly 127:quietly,indignant 128:smoothly 129:quietly,dryly 130:smoothly 131:quietly,dryly 132:whispers,gruffly 133:smoothly 134:smoothly 135:quietly 136:smoothly 137:quietly,frustrated 138:amused 139:quietly,sarcastic 140:smoothly 141:quietly 142:softly 143:whispers,sharply 144:whispers,dryly 145:whispers,sharply 146:whispers,dryly 147:whispers,dryly 148:whispers,dryly 149:whispers,intently 150:softly 151:whispers,excited 152:smoothly 153:smoothly 154:whispers,curious 155:softly,ominous 156:whispers,grumbling 157:quietly,intense 158:quietly,pointedly 159:quietly,sorrowful 160:quietly 161:softly 162:warning 163:quietly 164:quietly,haunted 166:softly 167:softly 168:whispers,intently 169:quietly 170:whispers 172:whispers,intently 173:sharply 174:whispers 175:quietly 176:whispers,dryly 177:whispers,dryly 178:quietly 179:smoothly 180:quietly,surprised 181:smoothly 182:quietly,urgently 183:softly 184:quietly 185:softly 186:quietly,insistent 187:softly 188:quietly,intense 189:whispers 190:softly 191:whispers,pointedly 192:softly 193:whispers,urgently 194:whispers,urgently 195:whispers,uneasy 196:quietly 197:whispers,uneasy 198:whispers,unsettled 200:dryly 201:intently 202:skeptical 203:firmly 204:skeptical 205:firmly 206:incredulous 207:calmly 208:grumbling 209:primly 210:sharply 211:evasive 212:exasperated 213:curious 214:quietly 215:dryly 216:ominous 217:urgently 218:gruffly 219:sharply 220:defensive 221:indignant 222:dismissively 223:indignant 224:dryly 225:suspicious 226:flatly 227:gently 228:quietly 229:gently 230:bitterly 231:gently 233:quietly,bitterly 234:whispers,uneasy 235:whispers 236:whispers,relieved 237:whispers,curious 238:whispers,dryly 239:whispers,grumbling 240:whispers,dryly 241:whispers,tense 242:whispers 243:whispers 244:whispers 245:whispers,skeptical 246:whispers 247:whispers 248:whispers,grimly 249:whispers 250:whispers,dryly 251:whispers 252:whispers,primly 253:whispers,exasperated 254:whispers,dryly 255:whispers,primly 256:whispers 257:whispers 258:whispers,grimly 259:whispers 260:whispers 261:whispers,intently 262:whispers 263:whispers,ominous 264:whispers,grimly 265:whispers,firmly 266:whispers 267:whispers 268:whispers 269:whispers 270:whispers,grimly 271:whispers 272:whispers,pointedly 273:whispers,dryly 274:whispers,primly 275:whispers,flatly 276:whispers 277:whispers,quietly 278:whispers 279:whispers,dryly 280:whispers,skeptical 281:whispers 282:whispers,dryly 283:whispers 284:whispers,grumbling 285:whispers,dryly 286:whispers,grumbling 287:whispers,dryly 288:whispers,sharply 289:whispers 290:whispers,uneasy 291:whispers 292:whispers 293:whispers 294:whispers,pointedly 295:whispers,urgently 296:whispers,sharply 297:whispers,flatly 298:whispers,indignant 299:whispers,uneasy 300:whispers,primly 301:whispers,alarmed 302:curious 303:evasive 304:exasperated 305:exasperated 306:tired 307:firmly 308:firmly 309:curious 310:grimly""",
21: """0:breathless,grumbling 1:dryly 2:grumbling 3:flatly 4:accusing 5:dryly 6:grumbling 7:sharply 8:primly 9:gruffly 10:primly
11:dryly 12:primly 13:gruffly 14:surprised 15:flatly 16:accusing 17:dryly 18:indignant 19:dryly 20:incredulous 21:evasive 22:skeptical
23:dryly 24:suspicious 25:dryly 26:grumbling 27:dryly 28:grumbling 29:dryly 30:curious 31:flatly 32:surprised 33:dryly 34:primly
35:dryly 36:uneasy 37:evasive 38:suspicious 39:evasive 40:uneasy 41:uneasy 42:intently 43:curious 44:uneasy 45:suspicious
46:dryly 47:dryly 48:tired 49:dryly 50:dryly 51:dryly 52:accusing 53:dryly 54:pointedly 55:defensive 56:pointedly 57:guarded
58:pointedly 59:evasive 60:sharply 61:dryly 62:firmly 63:evasive 64:firmly 65:dryly 66:firmly 67:defensive 68:insistent
69:dismissively 70:intense 71:defensive 72:firmly 73:dryly 74:whispers 75:quietly 76:quietly 77:quietly 78:quietly 79:flatly
80:pointedly 81:dryly 82:intently 83:evasive 84:dryly 85:reluctantly 86:intently 87:quietly 88:intently 89:quietly 90:intently
91:quietly 92:uneasy 93:fearful 94:curious 95:fearful 96:gruffly 97:exasperated 98:firmly 99:exasperated 100:accusing
101:dryly 102:intently 103:uneasy 104:primly 105:skeptical 106:dryly 107:curious 108:intently 109:gravely 110:dismissively
111:gravely 112:primly 113:curious 114:solemn 115:curious 116:solemn 117:curious 118:solemn 119:ominous 120:intently 121:quietly
122:intently 123:thoughtful 124:quietly 125:curious 126:guarded 127:dryly 128:dryly 129:dryly 130:awed 131:quietly 132:uneasy
133:quietly 134:ominous 135:quietly 136:gravely 137:curious 138:gravely 139:quietly 141:grumbling 142:primly 143:grumbling
144:curious 145:gravely 146:quietly 147:gravely 148:dryly 149:gravely 150:solemn 151:uneasy 152:quietly 153:curious 154:primly
155:dryly 156:thoughtful 157:thoughtful 158:dryly 159:quietly 160:dryly 161:quietly 162:skeptical 163:dryly 164:dryly
165:ominous 166:quietly 167:curious 168:ominous 169:quietly 170:awed 171:primly 172:incredulous 173:primly 174:curious
175:quietly 176:uneasy 178:uneasy 179:quietly 180:smoothly 182:quietly 183:ominous 184:skeptical 185:quietly 186:skeptical
187:primly 188:dryly 189:primly 190:sharply 191:dryly 192:grumbling 193:sharply 194:defensive 195:dryly 196:whispers
197:tense 198:solemn 199:fearful 200:urgently 201:confused 202:firmly 203:dryly 204:firmly 206:firmly 207:dismissively
208:firmly 209:annoyed 210:insistent 211:reluctantly""",
22: """0:intense 1:dismissively 2:indignant 3:flatly 4:gravely 5:coldly 6:gruffly 7:defensive 8:challenging 9:coldly 10:knowingly
11:exasperated 12:uneasy 13:quietly,solemn 14:quietly 15:whispers,uneasy 16:firmly,uneasy""",
23: """0:quietly,uneasy 2:curious 3:quietly 4:curious 5:quietly 6:dryly 7:pointedly 8:flatly 9:challenging 10:flatly 11:concerned
12:disgusted 13:uneasy 14:gravely 15:uneasy 16:grimly 17:quietly 18:whispers,alert 19:fearful 20:shouts 21:trembling 22:whispers,fearful
24:shaken 25:quietly 26:urgently 28:gravely 29:softly,ominous 30:sorrowful 31:eerie 32:solemn 33:ominous""",
24: """0:intently 1:curious 2:intently 3:curious 4:ominous 5:uneasy 6:excited 7:alert 8:intently 9:quietly 10:realizing 11:firmly
12:intense 13:intense 14:warning 15:firmly 16:quietly 17:firmly 18:whispers,fearful 19:whispers 20:whispers,uneasy 21:whispers
22:quietly,determined 24:shouts,fearful 25:firmly 26:weakly 27:shaken 28:dryly,weakly 29:firmly 30:urgently 31:quietly,fearful
32:confused 33:quietly 34:fearful 35:dryly 36:solemn 37:ominous""",
25: """0:groggy 1:quietly 2:curious 3:flatly 4:curious 5:uneasy 6:skeptical 7:uncertain 8:reassuring 9:flatly 10:amused
11:uneasy 12:firmly 13:uneasy 14:sharply 15:defensive 16:quietly 17:uneasy 18:urgently 19:quietly 20:grimly 21:firmly 22:firmly
23:intense 24:sharply 25:intense 26:flatly 27:intense 29:intense 30:excited 31:skeptical 33:accusing 34:intense 35:horrified
37:awed 38:curious 39:quietly 40:warmly,wistful 41:gently 42:quietly 43:quietly,bitterly 44:flatly 45:coldly 46:firmly
47:fearful 49:quietly 50:quietly 51:fearful""",
26: """0:awed 1:intently 4:quietly 5:intently 6:firmly 8:frustrated 9:frustrated 11:whispers,awed 12:whispers 13:whispers
15:whispers,fearful 16:whispers,ominous 17:uneasy 18:intently 19:grimly 20:quietly 21:quietly 22:intently 23:urgently
25:ominous 27:quietly,shaken""",
27: """0:firmly 1:firmly 2:uneasy 3:quietly 4:intently 5:quietly 6:quietly 9:hoarse,disbelieving 10:hoarse,dryly 11:cautiously
12:hoarse,dryly 13:gently 14:hoarse,weary 15:hoarse,weary 16:tense 17:hoarse 18:hoarse,ominous 19:shrewdly 20:hoarse 21:hoarse,weary
23:hoarse,sadly 25:hoarse,weary 26:hoarse,gravely 27:hoarse,ominous 29:gently 30:hoarse,weary 31:hoarse,resigned 32:quietly,shaken""",
28: """0:hoarse,knowingly 1:frustrated 2:hoarse 3:hoarse,dryly 4:tense 5:hoarse,weary 6:grumbling 7:hoarse,dryly 8:gruffly
9:hoarse,dryly 10:intently 11:intently 12:intently 13:quietly 14:quietly 15:uneasy 16:uneasy 17:hoarse,dryly 18:suspicious
19:hoarse,gravely 20:intently 21:quietly 22:quietly 25:hoarse,gravely 26:sharply 27:hoarse,weary 28:insistent 29:hoarse,sadly
30:tense 31:stunned 32:slowly 33:slowly,fearful 34:breathless 35:urgently 36:fearful 37:fearful 38:sharply 41:whispers""",
29: """1:flatly,desperate 2:concerned 4:concerned 7:gently 11:gently 13:quietly 17:alarmed 18:excited 20:puzzled 22:confused
24:confused 25:sharply 26:defensive 27:confused 29:uneasy 31:uneasy 33:sharply 34:frustrated 35:curious 36:quietly 37:urgently
38:quietly 39:firmly""",
30: """0:uneasy 1:quietly 2:fearful 3:dismissively 4:fearful 5:intently 6:defensive 9:quietly 10:firmly 11:concerned 16:firmly
17:quietly 18:quietly 19:tense 20:ominous 21:defiantly 22:skeptical 23:urgently 24:urgently 27:tense 28:quietly 29:distant""",
31: """0:quietly,distant 1:quietly,shaken 2:shaken 3:uncertain 4:fearful 6:thin 7:thin 8:fearful 10:quietly 11:confused""",
32: """0:confused 1:quietly 2:quietly 3:skeptical 4:confused 6:sharply 7:desperate 8:quietly 9:desperate 12:urgently 13:confused""",
33: """0:gruffly 1:impatient 5:confused 6:confused 7:confused 8:quietly""",
34: """0:quietly 1:quietly 2:quietly 3:quietly 4:vulnerable 5:quietly,uncertain 6:sadly 7:impatient 8:uneasy 11:quietly 12:quietly
13:quietly 14:gravely 15:quietly 16:quietly 17:quietly,uncertain""",
35: """1:defensive 4:quietly 5:quietly 6:impatient 7:frustrated 8:uneasy 10:uneasy 11:grimly 12:grimly 13:suspicious""",
36: """0:intently 1:quietly 2:urgently 4:hollow 5:hollow 6:uneasy 7:frustrated 8:quietly 9:uneasy 10:ominous 12:urgently 13:tense
14:quietly 15:dryly 16:dryly 21:dryly""",
37: """0:firmly 1:firmly 2:coolly 3:gruffly 4:intently 5:exasperated 6:intently 8:quietly 9:dryly 10:intently 11:intently 12:defensive
13:defensive 14:firmly 15:intently 18:sharply 20:intently 21:uncertain 22:intently 23:uncertain 24:pressing 25:uncertain 26:intently
27:protective 28:firmly 29:quietly 30:skeptical 31:firmly 32:gruffly 33:intense 34:intense 36:firmly 37:skeptical 38:determined
39:firmly 40:dryly 41:quietly 43:intently 44:satisfied 45:intently 46:approvingly 47:intently 48:intently 49:uneasy 50:quietly
51:quietly,ominous 52:intently 53:evasive 54:pointedly 55:uneasy 56:intently 59:uneasy 62:quietly 63:uneasy 64:intently
65:firmly 66:firmly 67:skeptical 68:firmly 70:firmly 71:gruffly 72:quietly 73:incredulous 74:quietly 76:intently 77:sarcastic
78:alarmed 79:calmly 80:worried 81:firmly 82:uneasy 83:quietly 85:firmly 86:firmly 87:quietly,worried 88:firmly 89:dryly
90:dryly 91:dryly 92:incredulous 93:primly 94:incredulous 95:firmly 96:uneasy 97:firmly 98:dryly 100:dryly 102:dryly
104:cheerfully 106:cheerfully 108:cheerfully 110:cheerfully 111:alert 112:uneasy 113:uneasy 114:quietly 115:uneasy 116:shaken
118:uneasy 119:breathless,shaken 121:intently 122:quietly 123:quietly 124:awed 125:quietly,fearful 126:whispers,urgently
127:whispers,urgently 129:whispers,fearful 131:whispers 132:whispers 133:whispers 134:confused""",
38: """0:tired,grumbling 1:grumbling 3:dryly 5:dryly 7:casually 9:quietly 10:quietly 11:quietly 12:intently 14:dryly 15:gruffly
16:patiently 17:defensive 18:pointedly 20:gently 21:grudgingly 22:quietly 23:quietly,ominous 25:curious 26:intently 27:intently
28:curious 29:firmly 30:excited 31:intently 32:intently 33:curious 34:grimly 35:knowingly 36:intently 37:dismissively 38:firmly
39:intently 40:curious 41:intently 42:skeptical 43:firmly 44:skeptical 45:firmly 46:quietly,ominous 47:concerned 48:defensive
49:knowingly 50:alarmed 51:fearful 53:intently 54:uneasy 55:quietly 56:ominous 58:tense 60:tense,dryly 61:urgently 62:strained
63:urgently 64:disturbed 65:urgently 66:strained 67:pressing 68:quietly 69:sharply 72:quietly,tense 76:confused 77:urgently
78:confused 84:strained,angrily 86:tense 89:whispers,tense 93:shaken 95:urgently 96:desperate 98:desperate 102:quietly
105:quietly 107:sharply 110:quietly 112:quietly 114:quietly 116:realizing 117:weakly,desperate 119:breathless 120:exhausted
121:desperate""",
39: """0:uneasy 1:distracted 2:uneasy 3:slowly 4:uneasy 5:confused 6:uncertain 7:uneasy 8:uncertain 9:shaken 10:quietly
11:quietly 12:shaken 13:insistent 14:quietly 15:quietly 16:unconvinced 17:surprised 18:quietly 19:wistful 20:sadly
21:firmly 22:quietly 23:whispers 24:firmly 25:uneasy 26:quietly 27:awed 28:awed 29:quietly 30:thoughtful 31:quietly
32:quietly 33:uneasy 34:gently 35:uncertain 36:thoughtful 37:softly 38:softly 39:quietly 40:hesitant 41:hesitant
42:quietly 43:grimly 44:quietly 45:troubled 46:uneasy 47:hollow 48:gently 49:flatly 50:gently 51:sharply 52:softly
53:quietly 54:quietly 55:quietly 56:gently 57:resolute 58:quietly 59:determined 60:uneasy 61:thoughtful 62:uneasy
63:quietly 64:thoughtful 65:quietly 66:quietly 67:awed 68:quietly 69:quietly 70:slowly 71:quietly 72:uneasy 73:quietly""",
40: """0:sharply 1:defensive 2:sharply 3:flatly 4:dryly 5:tense 6:skeptical 7:thoughtful 8:curious 9:dryly 10:dryly 11:dryly
12:firmly 13:alert 14:thoughtful 15:dryly 16:dryly 17:dryly 18:dryly 19:alert 20:tense 21:uneasy 22:tense 23:uneasy
24:firmly 25:quietly 26:urgently 27:quietly 28:tense 29:distantly 30:tense 31:quietly 32:urgently 33:distantly 34:sharply
35:quietly 36:sharply 37:quietly 38:alarmed 39:distantly 40:scared 41:distantly 42:hollow 43:alarmed 44:quietly
45:alarmed 46:quietly 47:uneasy 48:urgently 49:tense 50:uneasy 51:frustrated 52:urgently 53:quietly 54:urgently
55:quietly 56:urgently 57:distantly 58:alarmed 59:quietly 60:sharply 61:distantly 62:desperately 63:distantly
64:determined 65:pleading 66:strained 67:desperately 68:alarmed 69:distantly 70:uneasy 71:urgently 72:scared 73:urgently
74:strained 75:desperately 76:scared 77:hollow 78:urgently 79:desperately 80:distantly 81:desperately 82:wistful
83:pleading 84:quietly 85:desperately 86:strained 87:firmly 88:defiant 89:gently 90:defiant 91:quietly 92:desperately
93:gently 94:angrily 95:urgently 96:tearfully 97:gently 98:tearfully 99:gently 100:sorrowful 101:gently 102:fondly
103:tearfully,laughs 104:fondly 105:tearfully 106:urgently 107:quietly 108:determined 109:gently 110:tearfully 111:gently 112:whispers 113:whispers,sorrowful""",
}

def parse():
    out = {}
    for ch, spec in DIRECTION.items():
        d = {}
        for item in spec.split():
            idx, tags = item.split(':', 1)
            d[int(idx)] = [] if tags == '-' else tags.split(',')
        out[ch] = d
    return out
