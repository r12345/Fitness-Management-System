import { reactive, ref } from "vue";

export function useToast() {
  const message = ref("");
  const type = ref("success");
  let timer = null;

  function show(text, tone = "success") {
    message.value = text;
    type.value = tone;
    window.clearTimeout(timer);
    timer = window.setTimeout(function () {
      message.value = "";
    }, 2600);
  }

  return reactive({
    message,
    type,
    show
  });
}
