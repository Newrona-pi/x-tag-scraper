"use client";

import { useState, useEffect } from "react";
import FileUpload from "@/components/FileUpload";
import FormInput from "@/components/FormInput";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "error";
  progress: number;
  total: number;
  message: string;
  tweet_count?: number;
  error?: string;
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [keyword, setKeyword] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [limit, setLimit] = useState("100");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // 日付のデフォルト値を設定（今日から1年前まで）
  useEffect(() => {
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    setEndDate(today.toISOString().split("T")[0]);
    setStartDate(oneYearAgo.toISOString().split("T")[0]);
  }, []);

  // ポーリングをクリーンアップ
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      alert("JSONファイルを選択してください");
      return;
    }

    if (!keyword || !startDate || !endDate) {
      alert("すべての必須項目を入力してください");
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("keyword", keyword);
      formData.append("start_date", startDate);
      formData.append("end_date", endDate);
      formData.append("limit", limit);

      const response = await fetch(`${API_BASE_URL}/api/collect`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "リクエストに失敗しました");
      }

      const data = await response.json();
      setJobStatus({
        job_id: data.job_id,
        status: "pending",
        progress: 0,
        total: parseInt(limit),
        message: data.message,
      });

      // ポーリングを開始
      startPolling(data.job_id);
    } catch (error) {
      alert(`エラー: ${error instanceof Error ? error.message : "不明なエラー"}`);
      setIsSubmitting(false);
    }
  };

  const startPolling = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/status/${jobId}`);
        if (!response.ok) {
          throw new Error("ステータス取得に失敗しました");
        }

        const status: JobStatus = await response.json();
        setJobStatus(status);

        if (status.status === "completed" || status.status === "error") {
          clearInterval(interval);
          setIsSubmitting(false);
          setPollingInterval(null);
        }
      } catch (error) {
        console.error("ポーリングエラー:", error);
        clearInterval(interval);
        setIsSubmitting(false);
        setPollingInterval(null);
      }
    }, 2000); // 2秒ごとにポーリング

    setPollingInterval(interval);
  };

  const handleDownload = async () => {
    if (!jobStatus || jobStatus.status !== "completed") {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/download/${jobStatus.job_id}`);
      if (!response.ok) {
        throw new Error("ダウンロードに失敗しました");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tweets_${jobStatus.job_id}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert(`ダウンロードエラー: ${error instanceof Error ? error.message : "不明なエラー"}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white shadow-lg rounded-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            X タグスクレイパー
          </h1>
          <p className="text-gray-600 mb-8">
            X（旧Twitter）のハッシュタグ検索ツイートを収集します
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <FileUpload
              onFileSelect={setSelectedFile}
              selectedFile={selectedFile}
            />

            <FormInput
              label="キーワード / ハッシュタグ"
              type="text"
              value={keyword}
              onChange={setKeyword}
              placeholder="#Python / Python"
              required
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormInput
                label="開始日"
                type="date"
                value={startDate}
                onChange={setStartDate}
                required
                max={endDate}
              />

              <FormInput
                label="終了日"
                type="date"
                value={endDate}
                onChange={setEndDate}
                required
                min={startDate}
              />
            </div>

            <FormInput
              label="取得件数"
              type="number"
              value={limit}
              onChange={setLimit}
              placeholder="100"
              required
              min="1"
              max="10000"
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? "収集中..." : "ツイート収集を開始"}
            </button>
          </form>

          {jobStatus && (
            <div className="mt-8 p-6 bg-gray-50 rounded-lg">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                収集状況
              </h2>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>進捗</span>
                    <span>
                      {jobStatus.progress} / {jobStatus.total}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all ${
                        jobStatus.status === "completed"
                          ? "bg-green-500"
                          : jobStatus.status === "error"
                          ? "bg-red-500"
                          : "bg-blue-500"
                      }`}
                      style={{
                        width: `${(jobStatus.progress / jobStatus.total) * 100}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="text-sm text-gray-600">
                  <p>ステータス: {jobStatus.message}</p>
                  {jobStatus.tweet_count !== undefined && (
                    <p className="mt-1">
                      収集件数: {jobStatus.tweet_count}件
                    </p>
                  )}
                  {jobStatus.error && (
                    <p className="mt-1 text-red-600">エラー: {jobStatus.error}</p>
                  )}
                </div>

                {jobStatus.status === "completed" && (
                  <button
                    onClick={handleDownload}
                    className="w-full bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                  >
                    CSVをダウンロード
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
