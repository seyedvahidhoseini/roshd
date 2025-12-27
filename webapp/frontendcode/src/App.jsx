import React, { useEffect, useRef, useState } from "react";

// Backend base URL
const API_BASE = import.meta.env?.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  // --- freelancers ---
  const [freelancers, setFreelancers] = useState([]); // [{id,name,description,...}]
  const [selectedId, setSelectedId] = useState("");   // freelancer_id (== doc_id)
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState(null);
  const [creating, setCreating] = useState(false);
  const [loadingList, setLoadingList] = useState(false);

  // --- chat ---
  const [messages, setMessages] = useState([]); // {role:'user'|'assistant', text}
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  // load selectedId from storage
  useEffect(() => {
    const saved = localStorage.getItem("skillbot_freelancer_id");
    if (saved) setSelectedId(saved);
  }, []);
  useEffect(() => {
    if (selectedId) localStorage.setItem("skillbot_freelancer_id", selectedId);
  }, [selectedId]);

  // auto-scroll chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // fetch list
  const fetchFreelancers = async () => {
    setLoadingList(true);
    try {
      const res = await fetch(`${API_BASE}/freelancers`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "failed to fetch freelancers");
      setFreelancers(data.items || []);
    } catch (e) {
      console.error(e);
      alert(e.message);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    fetchFreelancers();
  }, []);

  // create freelancer (name + description + pdf)
  const createFreelancer = async () => {
    if (!name.trim()) return alert("نام فریلنسر را وارد کن");
    if (!file) return alert("فایل PDF را انتخاب کن");

    setCreating(true);
    try {
      const form = new FormData();
      form.append("name", name.trim());
      form.append("description", description.trim());
      form.append("file", file);

      const res = await fetch(`${API_BASE}/freelancers`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "ساخت فریلنسر ناموفق بود");

      const fr = data.freelancer;
      // به لیست اضافه کن و انتخابش کن
      setFreelancers((curr) => [fr, ...curr]);
      setSelectedId(fr.id);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `فریلنسر «${fr.name}» ساخته شد و مهارت‌ها ایندکس شدند. می‌تونی سوال بپرسی!` },
      ]);

      // پاک‌سازی فرم
      setName("");
      setDescription("");
      setFile(null);
      const inputEl = document.getElementById("fileInput");
      if (inputEl) inputEl.value = "";
    } catch (e) {
      alert(e.message);
    } finally {
      setCreating(false);
    }
  };

  const selectFreelancer = (id) => {
    setSelectedId(id);
    setMessages([]); // چت جدید
  };

  const sendMessage = async () => {
    if (!input.trim() || !selectedId) return;
    const userText = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text: userText }]);
    setSending(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ freelancer_id: selectedId, query: userText }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Chat error");
      setMessages((m) => [...m, { role: "assistant", text: data.answer }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `خطا: ${e.message}` },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearSelection = () => {
    setSelectedId("");
    localStorage.removeItem("skillbot_freelancer_id");
    setMessages([]);
  };

  const selected = freelancers.find((f) => f.id === selectedId);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900" dir="rtl">
      {/* Top Bar */}
      <header className="w-full border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg sm:text-xl font-semibold">چت بات مهارت های فریلنسرها</h1>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 grid gap-6 lg:grid-cols-3">
        {/* Create + List */}
        <section className="lg:col-span-1 space-y-6">
          {/* Create freelancer */}
          <div className="bg-white rounded-2xl shadow p-5 border">
            <h2 className="font-semibold mb-3">افزودن فریلنسر</h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm">نام</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-xl border px-3 py-2 text-sm"
                  placeholder="مثلاً: وحید"
                />
              </div>
              <div>
                <label className="text-sm">توضیحات</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="mt-1 w-full rounded-xl border px-3 py-2 text-sm"
                  placeholder="تخصص‌ها / نکات…"
                />
              </div>

              <div>
                <label className="text-sm block mb-1">فایل PDF مهارت</label>

                {/* input مخفی */}
                <input
                  id="fileInput"
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                />

                {/* ناحیه‌ی قابل‌کلیک با بوردر */}
                <label
                  htmlFor="fileInput"
                  className="flex items-center justify-between gap-3 w-full rounded-xl border-2 border-dashed border-gray-300 hover:border-blue-500 hover:bg-blue-50/50 transition cursor-pointer px-4 py-3"
                  title="برای انتخاب فایل کلیک کنید"
                >
                  <div className="text-sm">
                    {file ? (
                      <span className="font-medium">{file.name}</span>
                    ) : (
                      <span className="text-gray-500">برای انتخاب فایل کلیک کنید</span>
                    )}
                    <div className="text-xs text-gray-400 mt-0.5">فقط PDF</div>
                  </div>

                  <span className="shrink-0 rounded-lg border px-3 py-1 text-xs bg-white">
                    انتخاب فایل
                  </span>
                </label>
              </div>

              <button
                onClick={createFreelancer}
                disabled={creating}
                className={`w-full px-4 py-2 rounded-2xl text-white ${
                  creating ? "bg-gray-300" : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {creating ? "در حال ایجاد..." : "ایجاد فریلنسر"}
              </button>


            </div>
          </div>

          {/* List freelancers */}
          <div className="bg-white rounded-2xl shadow p-5 border">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold">فریلنسرها</h2>
              <button
                onClick={fetchFreelancers}
                className="text-xs px-2 py-1 rounded-lg bg-gray-100 hover:bg-gray-200"
                title="به‌روزرسانی لیست"
              >
                بروزرسانی
              </button>
            </div>

            {loadingList ? (
              <div className="text-sm text-gray-500">در حال دریافت...</div>
            ) : freelancers.length === 0 ? (
              <div className="text-sm text-gray-400">هنوز فریلنسری ثبت نشده.</div>
            ) : (
              <ul className="space-y-2 max-h-[260px] overflow-y-auto">
                {freelancers.map((f) => (
                  <li
                    key={f.id}
                    className={`p-3 rounded-xl border cursor-pointer transition ${
                      selectedId === f.id ? "bg-blue-50 border-blue-300" : "bg-white hover:bg-gray-50"
                    }`}
                    onClick={() => selectFreelancer(f.id)}
                    title={f.id}
                  >
                    <div className="text-sm font-medium">{f.name}</div>
                    {f.description && (
                      <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">{f.description}</div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* Chat */}
        <section className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow border flex flex-col h-[72vh]">
            <div className="px-5 py-3 border-b flex items-center justify-between">
              <div>
                <h2 className="font-semibold">چت با ربات</h2>
                {selected ? (
                  <div className="text-xs text-gray-500">{selected.name} - {selected.description}</div>
                ) : (
                  <div className="text-xs text-red-500">ابتدا یک فریلنسر انتخاب کن یا بساز</div>
                )}
              </div>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-sm text-gray-400">
                  برای شروع پیام ارسال کنید
                </div>
              ) : (
                messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-start" : "justify-end"}`}>
                    <div
                      className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${
                        m.role === "user" ? "bg-gray-100" : "bg-blue-50"
                      }`}
                    >
                      {m.text}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 border-t">
              <div className="flex items-end gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={selectedId ? "پیامت را بنویس..." : "ابتدا فریلنسر را انتخاب کن"}
                  disabled={!selectedId || sending}
                  rows={2}
                  className="flex-1 resize-none rounded-2xl border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-60"
                />
                <button
                  onClick={sendMessage}
                  disabled={!selectedId || sending || !input.trim()}
                  className={`px-4 py-2 rounded-2xl text-white ${
                    !selectedId || sending || !input.trim()
                      ? "bg-gray-300 cursor-not-allowed"
                      : "bg-blue-600 hover:bg-blue-700"
                  }`}
                >
                  {sending ? "در حال ارسال..." : "ارسال"}
                </button>
              </div>

            </div>
          </div>
        </section>
      </main>

    </div>
  );
}
