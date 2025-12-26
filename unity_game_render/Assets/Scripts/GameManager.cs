using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Diagnostics;

public class GameManager : MonoBehaviour
{   
    // =====================================================
    // Inspector Fields
    // =====================================================
    // Board Slots
    [Header("Board Slots (Order Matters)")]
    public GameObject[] blueBoard;
    public GameObject[] redBoard;

    // Item Prefabs
    [Header("Item Prefabs")]
    public GameObject magnifier;
    public GameObject cigarette;
    public GameObject beer;
    public GameObject saw;
    public GameObject handcuff;
    public GameObject phone;
    public GameObject reverse;

    [Header("Item Hint UI")]
    public ItemHintUI itemHintUI;
    // Gun
    [Header("Gun Reference")]
    public GameObject gun;

    // Bullet
    [Header("Bullet Slots")]
    public GameObject[] bulletSlot;

    [Header("Bullet Prefabs")]
    public GameObject liveBullet;
    public GameObject blankBullet;

    [Header("Bullet Hint UI")]
    public BulletHintUI bulletHintUI;

    // Computer
    [Header("Computer Display")]
    public GameObject computer;

    // Internal state
    int redHP  = 4;
    int blueHP = 4;
    TextMesh healthRedText;
    TextMesh healthBlueText;

    // Python Processes
    Process uartProcess;
    Process jsonProcess;

    // Maps
    Dictionary<string, GameObject> itemMap;
    Dictionary<string, string> spawnMap;
    Dictionary<string, string> itemNameMap;

    // Command system
    [Header("Auto Test Settings")]
    Queue<string> commandQueue = new Queue<string>();

    //Audio
    public static AudioManager I;
    // =====================================================
    // Unity Lifecycle
    // =====================================================
    void Awake()
    {
        InitMaps();

        InitComputerDisplay();

        StartPythonScripts();

        // 啟動指令執行 FSM
        StartCoroutine(CommandRunner());

        // 啟動資料夾輪詢
        StartCoroutine(CommandPoller());

    }

    void OnApplicationQuit()
    {
        StopPythonScripts();

        string scriptDir = Path.Combine(Application.dataPath, "..", "..", "python_code");
        string logsDir = Path.Combine(scriptDir, "game_logs");

        if (Directory.Exists(logsDir))
        {
            try
            {
                Directory.Delete(logsDir, true);
                UnityEngine.Debug.Log("Deleted game_logs folder.");
            }
            catch (System.Exception e)
            {
                UnityEngine.Debug.LogError($"Failed to delete game_logs: {e.Message}");
            }
        }
    }

    void StartPythonScripts()
    {
        string pythonPath = "python"; // Or full path to python.exe if not in PATH
        string scriptDir = Path.Combine(Application.dataPath, "..", "..", "python_code");
        
        // Start UART to JSON script
        string uartScript = Path.Combine(scriptDir, "python_uart_to_json.py");
        uartProcess = new Process();
        uartProcess.StartInfo.FileName = pythonPath;
        uartProcess.StartInfo.Arguments = $"\"{uartScript}\"";
        uartProcess.StartInfo.WorkingDirectory = scriptDir;
        uartProcess.StartInfo.UseShellExecute = false;
        uartProcess.StartInfo.CreateNoWindow = true; 
        uartProcess.Start();
        UnityEngine.Debug.Log("Started UART to JSON Python script.");

        // Start JSON to Command script
        string jsonScript = Path.Combine(scriptDir, "python_json_to_command.py");
        jsonProcess = new Process();
        jsonProcess.StartInfo.FileName = pythonPath;
        jsonProcess.StartInfo.Arguments = $"\"{jsonScript}\"";
        jsonProcess.StartInfo.WorkingDirectory = scriptDir;
        jsonProcess.StartInfo.UseShellExecute = false;
        jsonProcess.StartInfo.CreateNoWindow = true;
        jsonProcess.Start();
        UnityEngine.Debug.Log("Started JSON to Command Python script.");
    }

    void StopPythonScripts()
    {
        if (uartProcess != null && !uartProcess.HasExited)
        {
            uartProcess.Kill();
            uartProcess.Dispose();
            UnityEngine.Debug.Log("Stopped UART to JSON Python script.");
        }

        if (jsonProcess != null && !jsonProcess.HasExited)
        {
            jsonProcess.Kill();
            jsonProcess.Dispose();
            UnityEngine.Debug.Log("Stopped JSON to Command Python script.");
        }
    }
    // =====================================================
    // Command System / FSM
    // =====================================================
    IEnumerator CommandRunner()
    {
        while (true)
        {
            if (commandQueue.Count > 0)
            {
                string line = commandQueue.Dequeue();
                UnityEngine.Debug.Log($"[Runner] 執行 command: {line}");

                yield return StartCoroutine(ExecuteCommandLineCoroutine(line));
            }
            else
            {
                yield return null;
            }
        }
    }
    IEnumerator CommandPoller()
    {
        while (true)
        {
            LoadAndDeleteCommandsOnce();

            
            yield return new WaitForSeconds(0.2f);
        }
    }
    void LoadAndDeleteCommandsOnce()
    {
        string dirPath = Path.Combine(Application.dataPath, "..", "..", "Commands");

        if (!Directory.Exists(dirPath))
            return;

        string[] files = Directory.GetFiles(dirPath, "*.txt");
        System.Array.Sort(files);

        foreach (string file in files)
        {
            try
            {
                string line = File.ReadAllText(file).Trim();

                File.Delete(file);

                if (string.IsNullOrEmpty(line))
                    continue;

                commandQueue.Enqueue(line);

                UnityEngine.Debug.Log($"[CommandPoller] 新 command: {Path.GetFileName(file)} -> {line}");
            }
            catch (IOException)
            {
                // File might be in use by the external writer, skip and try next time
                continue;
            }
        }
    }
    // Execute one line of commands
    IEnumerator ExecuteCommandLineCoroutine(string line)
    {
        line = line.Trim();
        //Null
        if (string.IsNullOrEmpty(line))
            yield break;

        //Hp
        if (TryParseHealthCommand(line, out int red, out int blue))
        {
            SetHealthDirect(red, blue);
            yield break;
        }
        //Bullet
        if (TryParseBulletCommand(line, out int liveCnt, out int blankCnt))
        {
            yield return StartCoroutine(PlayBulletLoadCoroutine(liveCnt, blankCnt));
            yield break;
        }
        //load items
        if (line.StartsWith("["))
        {
            yield return StartCoroutine(ExecuteSpawnLineCoroutine(line));
            yield break;
        }
        //actions
        if (line.Length >= 2 &&TryDecodeSlotKey(line[0], out _, out _, out _) &&char.IsLetter(line[1]))
        {
            yield return StartCoroutine(ExecuteUseItemShortTokenCoroutine(line));
            yield break;
        }
        if (line.Length >= 2 && char.IsLetter(line[0]) && char.IsLetter(line[1]))
        {
            string[] tokens = line.Split(' ');
            foreach (string token in tokens)
                yield return StartCoroutine(ExecuteCommandTokenCoroutine(token));
        }
    }
    IEnumerator ExecuteUseItemShortTokenCoroutine(string token)
    {
        if (token.Length < 2)
            yield break;

        char slotKey  = token[0];
        char itemCode = char.ToUpper(token[1]);

        if (!TryDecodeSlotKey(slotKey, out GameObject[] board, out int slotIndex, out ItemSide side))
            yield break;

        ItemSlot slot = board[slotIndex].GetComponent<ItemSlot>();
        if (slot == null || slot.takenBy == null)
            yield break;

        if (slot.takenByName != itemCode.ToString())
        {
            UnityEngine.Debug.LogWarning(
                $"[Command] Slot has {slot.takenByName}, but command wants {itemCode}"
            );
            yield break;
        }
        
        if (itemNameMap.TryGetValue(itemCode.ToString(), out string itemName))
        {
            ShowItemHintByCommand(token, itemName);
        }
        else
        {
            itemHintUI.Show($"Use Item {itemCode}");
        }
        if (AudioManager.I != null)
        {
            switch (itemCode)
            {
                case 'M': AudioManager.I.PlaySFX(AudioManager.I.magnifier); break;
                case 'C': AudioManager.I.PlaySFX(AudioManager.I.cigarette); break;
                case 'B': AudioManager.I.PlaySFX(AudioManager.I.beer); break;
                case 'S': AudioManager.I.PlaySFX(AudioManager.I.saw); break;
                case 'H': AudioManager.I.PlaySFX(AudioManager.I.handcuff); break;
                case 'P': AudioManager.I.PlaySFX(AudioManager.I.phone); break;
                case 'R': AudioManager.I.PlaySFX(AudioManager.I.reverse); break;
            }
        }
        yield return PlayAtSlotCoroutine(board, slotIndex, side);
    }
    IEnumerator ExecuteCommandTokenCoroutine(string token)
    {
        token = token.Trim().ToUpper();

        if (token.Length < 2)
            yield break;

        char action = token[0];   // Q / E / T ...
        char hint   = token[1];   // L / B
        bool isLive = (hint == 'L');
        if (hint == 'L')
            bulletHintUI.Show("Live Bullet");
        else if (hint == 'B')
            bulletHintUI.Show("Blank Bullet");
        // === Blue shooter ===
        if (action == 'Q')
        {
            // Blue -> Blue, 1 dmg
            yield return PlayShootCoroutine(GunSide.Blue, GunSide.Blue, 1, isLive);
        }
        else if (action == 'W')
        {
            // Blue -> Blue, 2 dmg + regrow
            yield return PlayShootCoroutine(GunSide.Blue, GunSide.Blue, 2, isLive);
            yield return PlayRegrowCoroutine();
        }
        else if (action == 'E')
        {
            // Blue -> Red, 1 dmg
            yield return PlayShootCoroutine(GunSide.Blue, GunSide.Red, 1, isLive);
        }
        else if (action == 'R')
        {
            // Blue -> Red, 2 dmg + regrow
            yield return PlayShootCoroutine(GunSide.Blue, GunSide.Red, 2, isLive);
            yield return PlayRegrowCoroutine();
        }

        // === Red shooter ===
        else if (action == 'T')
        {
            // Red -> Blue, 1 dmg
            yield return PlayShootCoroutine(GunSide.Red, GunSide.Blue, 1, isLive);
        }
        else if (action == 'Y')
        {
            // Red -> Blue, 2 dmg + regrow
            yield return PlayShootCoroutine(GunSide.Red, GunSide.Blue, 2, isLive);
            yield return PlayRegrowCoroutine();
        }
        else if (action == 'U')
        {
            // Red -> Red, 1 dmg
            yield return PlayShootCoroutine(GunSide.Red, GunSide.Red, 1, isLive);
        }
        else if (action == 'I')
        {
            // Red -> Red, 2 dmg + regrow
            yield return PlayShootCoroutine(GunSide.Red, GunSide.Red, 2, isLive);
            yield return PlayRegrowCoroutine();
        }
    }
    // =====================================================
    // Parsing / Decode
    // =====================================================
    bool TryDecodeSlotKey(char key, out GameObject[] board, out int slotIndex, out ItemSide side)
    {
        board = null;
        slotIndex = -1;
        side = ItemSide.Blue;

        switch (key)
        {
            // Blue board
            case '1': board = blueBoard; slotIndex = 0; side = ItemSide.Blue; return true;
            case '2': board = blueBoard; slotIndex = 1; side = ItemSide.Blue; return true;
            case '3': board = blueBoard; slotIndex = 2; side = ItemSide.Blue; return true;
            case '4': board = blueBoard; slotIndex = 3; side = ItemSide.Blue; return true;
            case '5': board = blueBoard; slotIndex = 4; side = ItemSide.Blue; return true;
            case '6': board = blueBoard; slotIndex = 5; side = ItemSide.Blue; return true;

            // Red board
            case '7': board = redBoard; slotIndex = 0; side = ItemSide.Red; return true;
            case '8': board = redBoard; slotIndex = 1; side = ItemSide.Red; return true;
            case '9': board = redBoard; slotIndex = 2; side = ItemSide.Red; return true;
            case '0': board = redBoard; slotIndex = 3; side = ItemSide.Red; return true;
            case '-': board = redBoard; slotIndex = 4; side = ItemSide.Red; return true;
            case '=': board = redBoard; slotIndex = 5; side = ItemSide.Red; return true;
        }

        return false;
    }
    bool TryParseBulletCommand(string line, out int liveCount, out int blankCount)
    {
        liveCount = 0;
        blankCount = 0;

        line = line.Trim();

        if (!line.StartsWith("{") || !line.EndsWith("}"))
            return false;

        string content = line.Substring(1, line.Length - 2);
        string[] parts = content.Split(',');

        if (parts.Length != 2)
            return false;

        return int.TryParse(parts[0], out liveCount)
            && int.TryParse(parts[1], out blankCount);
    }
    bool TryParseHealthCommand(string line, out int red, out int blue)
    {
        red = 0;
        blue = 0;

        line = line.Trim();

        if (!line.StartsWith("(") || !line.EndsWith(")"))
            return false;

        string content = line.Substring(1, line.Length - 2);
        string[] parts = content.Split(',');

        if (parts.Length != 2)
            return false;

        return int.TryParse(parts[0], out red)
            && int.TryParse(parts[1], out blue);
    }
    void ShowItemHintByCommand(string token, string itemName)
    {
        char itemCode = token[1];

        switch (itemCode)
        {
            case 'M': // Magnifier: 0ML / 0MB
            {
                char bulletType = token[token.Length - 1];
                string msg = (bulletType == 'L')
                    ? "Next bullet is Live"
                    : "Next bullet is Blank";
                itemHintUI.Show(msg);
                break;
            }

            case 'C': // Cigarette
                itemHintUI.Show("Add 1 HP");
                break;

            case 'B': // Beer: 4BL / 4BB
            {
                char bulletType = token[token.Length - 1];
                string msg = (bulletType == 'L')
                    ? "Pop up Live Bullet"
                    : "Pop up Blank Bullet";
                itemHintUI.Show(msg);
                break;
            }

            case 'S': // Saw
                itemHintUI.Show("Double the damage");
                break;

            case 'H': // Handcuff
                itemHintUI.Show("Limit opponent 1 round");
                break;

            case 'P': // Phone: 9P5B
            {
                if (token.Length >= 4 &&
                    char.IsDigit(token[2]) &&
                    char.IsLetter(token[3]))
                {
                    int index = token[2] - '0';
                    string type = (token[3] == 'L') ? "Live" : "Blank";
                    itemHintUI.Show($"The {index}th bullet is {type}");
                }
                break;
            }

            case 'R': // Reverse
                itemHintUI.Show("Reverse next bullet");
                break;
        }
    }
    IEnumerator ExecuteSpawnLineCoroutine(string line)
    {
        ClearBoard();

        ExecuteSpawnLine(line); 

        yield return new WaitForSeconds(1.5f);
    }
    void ExecuteSpawnLine(string line)
    {
        int i = 0;
        while (i < line.Length)
        {
            if (line[i] == '[')
            {
                int end = line.IndexOf(']', i);
                if (end < 0) break;

                string token = line.Substring(i + 1, end - i - 1); 
                ExecuteSpawnToken(token);

                i = end + 1;
            }
            else
            {
                i++;
            }
        }
    }
    void ExecuteSpawnToken(string token)
    {
        // token format: B0:M
        if (token.Length < 4) return;

        char side = token[0];          // B or R
        int slotIndex = token[1] - '0';
        string itemCode = token.Substring(3, 1);

        GameObject[] board =
            (side == 'B') ? blueBoard :
            (side == 'R') ? redBoard  : null;

        if (board == null) return;
        if (slotIndex < 0 || slotIndex >= board.Length) return;

        SpawnOne(itemCode, board[slotIndex]);
    }

    // =====================================================
    // Item System
    // ====================================================
    void ClearBoard()
    {
        ClearOneSide(blueBoard);
        ClearOneSide(redBoard);
    }
    void ClearOneSide(GameObject[] board)
    {
        foreach (GameObject slotObj in board)
        {
            if (slotObj == null) continue;

            ItemSlot slot = slotObj.GetComponent<ItemSlot>();
            if (slot == null) continue;

            if (slot.takenBy != null)
            {
                Destroy(slot.takenBy);
                slot.takenBy = null;
            }
        }
    }
    void SpawnOne(string code, GameObject slotObj)
    {
        if (string.IsNullOrEmpty(code)) return;
        if (!itemMap.TryGetValue(code, out GameObject prefab)) return;
        if (!spawnMap.TryGetValue(code, out string spawnName)) return;

        Transform spawn = slotObj.transform.Find(spawnName);
        if (spawn == null)
        {
            UnityEngine.Debug.LogError($"Spawn '{spawnName}' not found under {slotObj.name}");
            return;
        }

        GameObject obj = Instantiate(prefab, spawn.position, spawn.rotation);

        ItemSlot slot = slotObj.GetComponent<ItemSlot>();
        if (slot != null)
        {
            slot.takenBy = obj;
            slot.takenByName = code;
        }
    }
    IEnumerator PlayAtSlotCoroutine(GameObject[] board, int slotIndex, ItemSide side)
    {
        if (slotIndex < 0 || slotIndex >= board.Length)
            yield break;

        ItemSlot slot = board[slotIndex].GetComponent<ItemSlot>();
        if (slot == null || slot.takenBy == null)
            yield break;

        ItemAnimator anim = slot.takenBy.GetComponent<ItemAnimator>();
        if (anim == null)
            yield break;

        anim.Play(side);

        yield return new WaitForSeconds(3.0f);
    }
    // =====================================================
    // Bullet System
    // =====================================================
    void ClearBulletSlots()
    {
        foreach (GameObject slotObj in bulletSlot)
        {
            if (slotObj == null) continue;

            BulletSlot slot = slotObj.GetComponent<BulletSlot>();
            if (slot == null) continue;

            if (slot.takenBy != null)
            {
                Destroy(slot.takenBy);
                slot.takenBy = null;
            }

            slot.isLive = false;
        }
    }
    void SpawnBulletAtSlot(int index, bool isLive)
    {
        if (index < 0 || index >= bulletSlot.Length)
            return;

        GameObject slotObj = bulletSlot[index];
        BulletSlot slot = slotObj.GetComponent<BulletSlot>();
        if (slot == null) return;

        Transform spawn = slotObj.transform.Find("Bullet Spawn");
        if (spawn == null)
        {
            UnityEngine.Debug.LogError($"BulletSpawn not found under {slotObj.name}");
            return;
        }

        GameObject prefab = isLive ? liveBullet : blankBullet;

        GameObject bullet = Instantiate(
            prefab,
            spawn.position,
            spawn.rotation,
            spawn
        );

        slot.takenBy = bullet;
        slot.isLive  = isLive;
    }
    void LoadBulletsByCommand(int liveCount, int blankCount)
    {
        ClearBulletSlots();

        int slotIndex = 0;

        // Live bullets
        for (int i = 0; i < liveCount && slotIndex < bulletSlot.Length; i++)
        {
            SpawnBulletAtSlot(slotIndex, true);
            slotIndex++;
        }

        // Blank bullets
        for (int i = 0; i < blankCount && slotIndex < bulletSlot.Length; i++)
        {
            SpawnBulletAtSlot(slotIndex, false);
            slotIndex++;
        }

        UnityEngine.Debug.Log($"[Bullet] Loaded {liveCount} live + {blankCount} blank bullets");
    }
    IEnumerator PlayBulletLoadCoroutine(int liveCount, int blankCount)
    {
        LoadBulletsByCommand(liveCount, blankCount);

        yield return new WaitForSeconds(2.0f);

        if (AudioManager.I != null)
            AudioManager.I.PlaySFX(AudioManager.I.bulletLoad);

        yield return new WaitForSeconds(1.0f);

        ClearBulletSlots();
    }
    // =====================================================
    // Gun System
    // =====================================================
    IEnumerator PlayShootCoroutine(GunSide shooter, GunSide target, int damage, bool isLive)
    {
        if (gun == null)
            yield break;

        GunAnimator gAnim = gun.GetComponent<GunAnimator>();
        if (gAnim == null)
            yield break;

        gAnim.PlayShoot(shooter, target, damage);

        yield return new WaitForSeconds(2.5f);

        if (AudioManager.I != null)
        {
            if (isLive)
                AudioManager.I.PlaySFX(AudioManager.I.gunShootLive);
            else
                AudioManager.I.PlaySFX(AudioManager.I.gunShootBlank);
        }

        yield return new WaitForSeconds(1.0f);
    }
    IEnumerator PlayRegrowCoroutine()
    {
        if (gun == null)
            yield break;

        GunAnimator gAnim = gun.GetComponent<GunAnimator>();
        if (gAnim == null)
            yield break;

        gAnim.PlayRegrow();

        yield return new WaitForSeconds(1f);
    }
    // =====================================================
    // Computer / UI
    // =====================================================
    void InitComputerDisplay()
    {
        if (computer == null)
        {
            UnityEngine.Debug.LogError("Computer not assigned!");
            return;
        }

        Transform red = computer.transform.Find("HealthRed");
        Transform blue = computer.transform.Find("HealthBlue");

        if (red != null)
            healthRedText = red.GetComponent<TextMesh>();

        if (blue != null)
            healthBlueText = blue.GetComponent<TextMesh>();
    }
    void SetHealthDirect(int red, int blue)
    {
        redHP = Mathf.Max(0, red);
        blueHP = Mathf.Max(0, blue);

        UpdateRedHealthDisplay();
        UpdateBlueHealthDisplay();
    }
    void UpdateRedHealthDisplay()
    {
        if (healthRedText != null)
            healthRedText.text = redHP.ToString();
    }

    void UpdateBlueHealthDisplay()
    {
        if (healthBlueText != null)
            healthBlueText.text = blueHP.ToString();
    }
    // =====================================================
    // Ambience Music
    // =====================================================
    void Start()
    {
        if (AudioManager.I != null)
            AudioManager.I.PlayAmbience();
    }
    // =====================================================
    // Init / Utilities
    // =====================================================
    void InitMaps()
    {
        itemMap = new Dictionary<string, GameObject>
        {
            { "M", magnifier },
            { "C",  cigarette },
            { "B", beer },
            { "S",  saw },
            { "H", handcuff },
            { "P",  phone },
            { "R", reverse },
        };

        spawnMap = new Dictionary<string, string>
        {
            { "M", "Magnifier Spawn" },
            { "C",  "Cigarette Spawn" },
            { "B", "Beer Spawn" },
            { "S",  "Saw Spawn" },
            { "H", "Handcuff Spawn" },
            { "P",  "Phone Spawn" },
            { "R", "Reverse Spawn" },
        };
        itemNameMap = new Dictionary<string, string>
        {
            { "M", "Magnifier" },
            { "C", "Cigarette" },
            { "B", "Beer" },
            { "S", "Saw" },
            { "H", "Handcuff" },
            { "P", "Phone" },
            { "R", "Reverse" },
        };
    }
}

