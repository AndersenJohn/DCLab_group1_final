using UnityEngine;
using TMPro;
using System.Collections;

public class ItemHintUI : MonoBehaviour
{
    public TextMeshProUGUI hintText;
    Coroutine currentRoutine;

    public void Show(string message, float duration = 2.0f)
    {
        if (currentRoutine != null)
            StopCoroutine(currentRoutine);

        currentRoutine = StartCoroutine(ShowRoutine(message, duration));
    }

    IEnumerator ShowRoutine(string message, float duration)
    {
        hintText.gameObject.SetActive(true);
        hintText.text = message;

        yield return new WaitForSeconds(duration);

        hintText.text = "";
    }
}
