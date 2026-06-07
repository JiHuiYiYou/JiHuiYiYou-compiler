#include <iostream>

using namespace std;

// =====================
// FFI（JHYY 侧用 extern）
// =====================
void print(const char* msg) {
    cout << msg;
}

// =====================
// 枚举（JHYY enum）
// =====================
enum GameState {
    STATE_PLAYING,
    STATE_WIN,
    STATE_LOSE
};

enum RoomType {
    ROOM_START,
    ROOM_MONSTER,
    ROOM_HEAL,
    ROOM_TREASURE,
    ROOM_BOSS,
    ROOM_EXIT
};

enum MonsterType {
    MONSTER_SLIME,
    MONSTER_SKELETON,
    MONSTER_DRAGON
};

enum Action {
    ACTION_ATTACK,
    ACTION_HEAL,
    ACTION_RUN
};

// =====================
// 结构体（JHYY struct）
// =====================
struct Player {
    int hp;
    int maxHp;
    int atk;
    int potions;
};

struct Monster {
    MonsterType type;
    int hp;
    int atk;
    int gold;
};

// =====================
// 全局状态（JHYY 支持）
// =====================
Player g_player;
Monster g_monster;
GameState g_state;
int g_roomIndex;
int g_gold;

// =====================
// 工具函数
// =====================
int clamp(int x, int min, int max) {
    if (x < min) return min;
    if (x > max) return max;
    return x;
}

int randRange(int min, int max) {
    static int seed = 12345;
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return min + (seed % (max - min + 1));
}

// =====================
// 玩家
// =====================
void playerInit() {
    g_player.hp = 20;
    g_player.maxHp = 20;
    g_player.atk = 4;
    g_player.potions = 2;
}

void playerHeal(int amount) {
    g_player.hp += amount;
    g_player.hp = clamp(g_player.hp, 0, g_player.maxHp);
}

// =====================
// 怪物
// =====================
void monsterSpawn(MonsterType type) {
    g_monster.type = type;

    if (type == MONSTER_SLIME) {
        g_monster.hp = 8;
        g_monster.atk = 2;
        g_monster.gold = 5;
    } else if (type == MONSTER_SKELETON) {
        g_monster.hp = 14;
        g_monster.atk = 4;
        g_monster.gold = 10;
    } else {
        g_monster.hp = 30;
        g_monster.atk = 7;
        g_monster.gold = 50;
    }
}

// =====================
// 房间描述
// =====================
void describeRoom(RoomType room) {
    if (room == ROOM_START) {
        print("你站在地牢入口。\n");
    } else if (room == ROOM_MONSTER) {
        print("一只怪物冲了出来！\n");
    } else if (room == ROOM_HEAL) {
        print("你发现了治疗泉水。\n");
    } else if (room == ROOM_TREASURE) {
        print("你找到了一个宝箱。\n");
    } else if (room == ROOM_BOSS) {
        print("前方是最终 BOSS 房间。\n");
    } else {
        print("你看到了出口。\n");
    }
}

// =====================
// 战斗系统
// =====================
void battle() {
    while (g_player.hp > 0 && g_monster.hp > 0) {
        cout << "\n你的 HP: " << g_player.hp
             << "/" << g_player.maxHp << endl;
        cout << "怪物 HP: " << g_monster.hp << endl;

        print("1. 攻击\n");
        print("2. 喝药 (+6 HP)\n");
        print("3. 逃跑\n");
        print("选择行动：");

        int choice;
        cin >> choice;

        if (choice == 1) {
            int dmg = g_player.atk + randRange(-1, 1);
            g_monster.hp -= dmg;
            cout << "你造成了 " << dmg << " 点伤害。\n";
        } else if (choice == 2) {
            if (g_player.potions > 0) {
                playerHeal(6);
                g_player.potions--;
                print("你喝下一瓶药。\n");
            } else {
                print("你没有药水！\n");
                continue;
            }
        } else if (choice == 3) {
            if (randRange(0, 1) == 0) {
                print("逃跑失败！\n");
            } else {
                print("你逃跑了。\n");
                return;
            }
        }

        if (g_monster.hp > 0) {
            int dmg = g_monster.atk + randRange(-1, 1);
            g_player.hp -= dmg;
            cout << "怪物造成了 " << dmg << " 点伤害。\n";
        }
    }

    if (g_player.hp <= 0) {
        g_state = STATE_LOSE;
    } else {
        print("你击败了怪物！\n");
        g_gold += g_monster.gold;
    }
}

// =====================
// 房间逻辑
// =====================
void processRoom(RoomType room) {
    describeRoom(room);

    if (room == ROOM_HEAL) {
        playerHeal(8);
        print("你恢复了生命值。\n");
    } else if (room == ROOM_TREASURE) {
        g_gold += 20;
        g_player.potions++;
        print("获得金币和药水。\n");
    } else if (room == ROOM_MONSTER) {
        monsterSpawn(MONSTER_SLIME);
        battle();
    } else if (room == ROOM_BOSS) {
        monsterSpawn(MONSTER_DRAGON);
        battle();
    } else if (room == ROOM_EXIT) {
        g_state = STATE_WIN;
    }
}

// =====================
// 主函数
// =====================
int main() {
    playerInit();
    g_state = STATE_PLAYING;
    g_roomIndex = 0;
    g_gold = 0;

    print("=== 地下城文字 Rogue ===\n");

    while (g_state == STATE_PLAYING) {
        RoomType room;

        if (g_roomIndex == 0) room = ROOM_START;
        else if (g_roomIndex == 1) room = ROOM_HEAL;
        else if (g_roomIndex == 2) room = ROOM_MONSTER;
        else if (g_roomIndex == 3) room = ROOM_TREASURE;
        else if (g_roomIndex == 4) room = ROOM_BOSS;
        else room = ROOM_EXIT;

        processRoom(room);

        if (g_state == STATE_PLAYING) {
            print("\n前往下一层？(1=是 0=退出)：");
            int go;
            cin >> go;
            if (go == 0) break;
            g_roomIndex++;
        }
    }

    if (g_state == STATE_WIN) {
        print("\n🎉 你成功逃出地牢！\n");
    } else {
        print("\n💀 你死在了地牢深处。\n");
    }

    cout << "最终金币：" << g_gold << endl;
    return 0;
}