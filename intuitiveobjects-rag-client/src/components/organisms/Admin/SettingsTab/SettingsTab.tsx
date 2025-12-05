import { useEffect, useState } from "react";
import { Button } from "@/components/atoms/Button/Button";
import { Select } from "@/components/atoms/Select/Select";
import { TextArea } from "@/components/atoms/TextArea/TextArea";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  settingGetAppConfigApi,
  settingUpdateAppConfigApi,
  settingGetAppCurrentConfigApi,
} from "@/services/adminApi";
import { toast } from "react-hot-toast";
import { Settings, Save, Zap } from "lucide-react";
import { motion } from "framer-motion";

interface SystemSettings {
  llm_model: string;
  embedding_model: string;
  query_model?: string;
  tags_model?: string;
  system_prompt: string;
  temperature: number;
}

export const SettingsTab = () => {
  const [settings, setSettings] = useState<SystemSettings>({
    llm_model: "",
    embedding_model: "",
    query_model: "",
    tags_model: "",
    system_prompt: "",
    temperature: 0.0,
  });

  const dispatch = useAppDispatch();
  const { appConfig, currentAppConfig } = useAppSelector(
    (state: any) => state.admin
  );

  useEffect(() => {
    dispatch(settingGetAppConfigApi());
    dispatch(settingGetAppCurrentConfigApi());
  }, []);

  const handleSaveSettings = () => {
    dispatch(settingUpdateAppConfigApi(settings));
    toast.success("Settings saved successfully");
    setSettings({
      llm_model: "",
      embedding_model: "",
      query_model: "",
      tags_model: "",
      system_prompt: "",
      temperature: 0.0,
    });
  };

  const isFormValid = () => {
    return (
      settings.llm_model.trim() !== "" &&
      settings.embedding_model.trim() !== "" &&
      settings.query_model?.trim() !== "" &&
      settings.tags_model?.trim() !== "" &&
      settings.system_prompt.trim() !== "" &&
      settings.temperature >= 0.0 &&
      settings.temperature <= 1.0
    );
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          <h1 className="text-3xl font-bold gradient-text">System Settings</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Configure your AI model and system behavior
        </p>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* LLM Model Selection */}
        <motion.div variants={itemVariants} className="card">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-accent-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              LLM Model
            </h2>
          </div>
          <Select
            value={settings.llm_model}
            onChange={(e) =>
              setSettings({ ...settings, llm_model: e.target.value })
            }
            className="w-full"
          >
            <option value="">Select LLM model</option>
            <option value="qwen2.5:1.5b">qwen2.5:1.5b</option>
            <option value="phi4-mini:3.8b">phi4-mini:3.8b</option>
            <option value="gemma3:4b">gemma3:4b</option>
            <option value="gemma2:2b">gemma2:2b</option>
            <option value="deepseek-coder:1.3b">deepseek-coder:1.3b</option>
            {appConfig &&
              appConfig.length &&
              appConfig[0]?.llm_models.map((option: any) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
          </Select>
        </motion.div>

        {/* Embedding Model Selection */}
        <motion.div variants={itemVariants} className="card">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-accent-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Embedding Model
            </h2>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            (Optional)
          </p>
          <Select
            value={settings.embedding_model}
            onChange={(e) =>
              setSettings({ ...settings, embedding_model: e.target.value })
            }
            className="w-full"
          >
            <option value="">Select embedding model</option>
            <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2</option>
            {appConfig &&
              appConfig.length &&
              appConfig[0]?.embedding_models?.map((option: any) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
          </Select>
        </motion.div>

        {/*Query Expand Model Selection */}
        <motion.div variants={itemVariants} className="card">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-accent-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              LLM Model For Query Expansion
            </h2>
          </div>
          <Select
            value={settings.query_model}
            onChange={(e) =>
              setSettings({ ...settings, query_model: e.target.value })
            }
            className="w-full"
          >
            <option value="">Select LLM model</option>
            <option value="qwen3:8b">qwen3:8b</option>
            <option value="gemma3:4b">gemma3:4b</option>
            {appConfig &&
              appConfig.length &&
              appConfig[0]?.query_models.map((option: any) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
          </Select>
        </motion.div>

        {/*Tags Model Selection */}
        <motion.div variants={itemVariants} className="card">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-accent-500" /> 
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              LLM Model For Tags Generation
            </h2>
          </div>
          <Select
            value={settings.tags_model}
            onChange={(e) =>  
              setSettings({ ...settings, tags_model: e.target.value })
            }
            className="w-full"
          > 
            <option value="">Select LLM model</option>
            <option value="llama2:latest">llama2:latest</option>
            <option value="phi4-mini:3.8b">phi4-mini:3.8b</option>  
            {appConfig &&
              appConfig.length &&
              appConfig[0]?.tags_models.map((option: any) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))} 
          </Select>
        </motion.div>

        {/* System Prompt */}
        <motion.div variants={itemVariants} className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Prompt
          </h2>
          <TextArea
            value={settings.system_prompt}
            onChange={(e) =>
              setSettings({ ...settings, system_prompt: e.target.value })
            }
            placeholder="Enter system prompt..."
            rows={6}
            className="w-full"
          />
        </motion.div>

        {/* Temperature Setting */}
        <motion.div variants={itemVariants} className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Temperature
          </h2>
          <div className="space-y-3">
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.temperature}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  temperature: parseFloat(e.target.value),
                })
              }
              className="w-full"
            />
            <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
              <span>More Deterministic (0)</span>
              <span className="text-lg font-semibold text-primary-600 dark:text-primary-400">
                {settings.temperature.toFixed(1)}
              </span>
              <span>More Random (1)</span>
            </div>
          </div>
        </motion.div>

        {/* Save Button */}
        <motion.div variants={itemVariants}>
          <Button
            onClick={handleSaveSettings}
            disabled={!isFormValid()}
            className="w-full btn-primary flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save Settings
          </Button>
        </motion.div>
      </motion.div>

      {/* Current Settings Display */}
      {currentAppConfig && (
        <motion.div
          variants={itemVariants}
          className="card mt-8 bg-gradient-to-br from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 border-2 border-primary-200 dark:border-primary-800"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Current Configuration
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-white dark:bg-gray-800">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                LLM Model
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentAppConfig?.llm_model || "Not set"}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white dark:bg-gray-800">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Embedding Model
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentAppConfig?.embedding_model || "Not set"}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white dark:bg-gray-800">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Query Expand Model  
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentAppConfig?.query_model || "Not set"}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white dark:bg-gray-800">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Tags Model
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {currentAppConfig?.tags_model || "Not set"}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white dark:bg-gray-800 md:col-span-2">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                System Prompt
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                {currentAppConfig?.system_prompt || "Not set"}
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white dark:bg-gray-800">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                Temperature
              </p>
              <p className="text-lg font-semibold text-primary-600 dark:text-primary-400">
                {currentAppConfig?.temperature || "Not set"}
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};
