import { useState, useEffect } from 'react'
import { useConfigStore } from '@/store/configStore'
import { configApi } from '@/services/configApi'
import { auditApi } from '@/services/auditApi'
import { Card } from '@/components/Card'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Modal } from '@/components/Modal'
import { ViolationType } from '@/types'
import type { ThresholdConfig } from '@/types'

const violationTypeLabels: Record<string, string> = {
  [ViolationType.Scam]: 'Scam',
  [ViolationType.Harassment]: 'Harassment',
  [ViolationType.FakeProfile]: 'Fake Profile',
  [ViolationType.SelfHarm]: 'Self Harm',
  [ViolationType.IllegalActivity]: 'Illegal Activity',
  [ViolationType.ChildSafety]: 'Child Safety',
  [ViolationType.BotFarm]: 'Bot Farm',
  [ViolationType.RepeatOffender]: 'Repeat Offender',
}

const selectableViolationTypes = Object.values(ViolationType).filter(
  (v) => v !== ViolationType.Unknown,
)

export function AdminConfigPage() {
  const { configs, loading, fetchConfigs, rollback } = useConfigStore()

  const [selectedViolationType, setSelectedViolationType] = useState<ViolationType>(
    ViolationType.Scam,
  )
  const [autonomousThreshold, setAutonomousThreshold] = useState(0.9)
  const [investigationThreshold, setInvestigationThreshold] = useState(0.5)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  const [rollbackModal, setRollbackModal] = useState<{
    open: boolean
    config_key: string
    version_id: string
  }>({ open: false, config_key: '', version_id: '' })

  const [exportStartDate, setExportStartDate] = useState('')
  const [exportEndDate, setExportEndDate] = useState('')
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json')
  const [exportError, setExportError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    fetchConfigs()
  }, [fetchConfigs])

  async function handleSaveThresholds() {
    setSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    const config: ThresholdConfig = {
      violation_type: selectedViolationType,
      autonomous_threshold: autonomousThreshold,
      investigation_trigger_threshold: investigationThreshold,
    }

    try {
      await configApi.updateThresholds(config)
      await fetchConfigs()
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (e) {
      setSaveError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  async function handleRollbackConfirm() {
    try {
      await rollback(rollbackModal.config_key, rollbackModal.version_id)
      setRollbackModal({ open: false, config_key: '', version_id: '' })
    } catch {
      // Error is handled by the store
    }
  }

  async function handleExport() {
    if (!exportStartDate || !exportEndDate) return

    setExporting(true)
    setExportError(null)

    try {
      const { download_url } = await auditApi.exportLogs(
        exportStartDate,
        exportEndDate,
        exportFormat,
      )
      window.open(download_url, '_blank')
    } catch (e) {
      setExportError((e as Error).message)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configuration Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage thresholds, view active configurations, and export audit logs.
        </p>
      </div>

      {/* Threshold Editor */}
      <Card title="Threshold Editor">
        <div className="space-y-4">
          <div>
            <label htmlFor="violation-type" className="block text-sm font-medium text-gray-700">
              Violation Type
            </label>
            <select
              id="violation-type"
              value={selectedViolationType}
              onChange={(e) => setSelectedViolationType(e.target.value as ViolationType)}
              className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
            >
              {selectableViolationTypes.map((vt) => (
                <option key={vt} value={vt}>
                  {violationTypeLabels[vt] ?? vt}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="autonomous-threshold"
                className="block text-sm font-medium text-gray-700"
              >
                Autonomous Threshold
              </label>
              <input
                id="autonomous-threshold"
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={autonomousThreshold}
                onChange={(e) => setAutonomousThreshold(parseFloat(e.target.value))}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
              />
              <p className="mt-1 text-xs text-gray-500">
                Confidence required for autonomous enforcement (0.0 - 1.0)
              </p>
            </div>

            <div>
              <label
                htmlFor="investigation-threshold"
                className="block text-sm font-medium text-gray-700"
              >
                Investigation Trigger Threshold
              </label>
              <input
                id="investigation-threshold"
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={investigationThreshold}
                onChange={(e) => setInvestigationThreshold(parseFloat(e.target.value))}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
              />
              <p className="mt-1 text-xs text-gray-500">
                Anomaly score that triggers investigation (0.0 - 1.0)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveThresholds}
              disabled={saving}
              className="inline-flex items-center rounded-lg bg-midnight px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-aubergine focus:outline-none focus:ring-2 focus:ring-midnight focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Thresholds'}
            </button>

            {saveSuccess && (
              <span className="text-sm font-medium text-green-600">
                Thresholds saved successfully.
              </span>
            )}
            {saveError && (
              <span className="text-sm font-medium text-red-600">Error: {saveError}</span>
            )}
          </div>
        </div>
      </Card>

      {/* Active Configurations */}
      <Card title="Active Configurations">
        {loading ? (
          <LoadingSpinner />
        ) : configs.length === 0 ? (
          <p className="text-sm text-gray-500">No configurations found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 pr-4 font-medium text-gray-500">Violation Type</th>
                  <th className="pb-3 pr-4 font-medium text-gray-500">Autonomous Threshold</th>
                  <th className="pb-3 pr-4 font-medium text-gray-500">Investigation Trigger</th>
                  <th className="pb-3 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {configs.map((config) => {
                  const val = config.value || {}
                  return (
                    <tr key={config.config_key}>
                      <td className="py-3 pr-4 font-medium text-gray-900 capitalize">
                        {(val.violation_type as string || config.config_key).replace(/_/g, ' ')}
                      </td>
                      <td className="py-3 pr-4 font-mono text-gray-700">
                        {String(val.autonomous_threshold ?? '--')}
                      </td>
                      <td className="py-3 pr-4 font-mono text-gray-700">
                        {String(val.investigation_trigger_threshold ?? '--')}
                      </td>
                      <td className="py-3">
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                          Active
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Audit Export */}
      <Card title="Audit Export">
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="export-start" className="block text-sm font-medium text-gray-700">
                Start Date
              </label>
              <input
                id="export-start"
                type="date"
                value={exportStartDate}
                onChange={(e) => setExportStartDate(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
              />
            </div>
            <div>
              <label htmlFor="export-end" className="block text-sm font-medium text-gray-700">
                End Date
              </label>
              <input
                id="export-end"
                type="date"
                value={exportEndDate}
                onChange={(e) => setExportEndDate(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
              />
            </div>
          </div>

          <div>
            <span className="block text-sm font-medium text-gray-700">Format</span>
            <div className="mt-2 flex items-center gap-6">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="exportFormat"
                  value="json"
                  checked={exportFormat === 'json'}
                  onChange={() => setExportFormat('json')}
                  className="h-4 w-4 border-gray-300 text-midnight focus:ring-midnight"
                />
                JSON
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="radio"
                  name="exportFormat"
                  value="csv"
                  checked={exportFormat === 'csv'}
                  onChange={() => setExportFormat('csv')}
                  className="h-4 w-4 border-gray-300 text-midnight focus:ring-midnight"
                />
                CSV
              </label>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExport}
              disabled={exporting || !exportStartDate || !exportEndDate}
              className="inline-flex items-center rounded-lg bg-midnight px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-aubergine focus:outline-none focus:ring-2 focus:ring-midnight focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : 'Export Audit Logs'}
            </button>

            {exportError && (
              <span className="text-sm font-medium text-red-600">Error: {exportError}</span>
            )}
          </div>
        </div>
      </Card>

      {/* Rollback Confirmation Modal */}
      <Modal
        open={rollbackModal.open}
        onClose={() => setRollbackModal({ open: false, config_key: '', version_id: '' })}
        title="Confirm Rollback"
      >
        <p className="text-sm text-gray-600">
          Are you sure you want to rollback{' '}
          <span className="font-semibold text-gray-900">{rollbackModal.config_key}</span> to
          version{' '}
          <span className="font-mono text-xs font-semibold text-gray-900">
            {rollbackModal.version_id}
          </span>
          ?
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setRollbackModal({ open: false, config_key: '', version_id: '' })}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleRollbackConfirm}
            disabled={loading}
            className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-amber-700 disabled:opacity-50"
          >
            {loading ? 'Rolling back...' : 'Confirm Rollback'}
          </button>
        </div>
      </Modal>
    </div>
  )
}
