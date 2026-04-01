import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  StyleSheet,
} from "react-native";
import { Colors, Spacing, BorderRadius, FontSize } from "../constants/theme";

interface Props {
  label: string;
  value: string; // ISO "YYYY-MM-DD"
  onChange: (date: string) => void;
  minDate?: string;
}

const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function DatePickerModal({ label, value, onChange, minDate }: Props) {
  const [open, setOpen] = useState(false);

  const parsed = value ? new Date(value + "T00:00:00") : new Date();
  const [viewYear, setViewYear] = useState(parsed.getFullYear());
  const [viewMonth, setViewMonth] = useState(parsed.getMonth());

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const minD = minDate ? new Date(minDate + "T00:00:00") : today;

  function prevMonth() {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(y => y - 1); }
    else setViewMonth(m => m - 1);
  }
  function nextMonth() {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(y => y + 1); }
    else setViewMonth(m => m + 1);
  }

  function buildCalendar() {
    const firstDay = new Date(viewYear, viewMonth, 1).getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const cells: (number | null)[] = [];
    for (let i = 0; i < firstDay; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    return cells;
  }

  function selectDay(day: number) {
    const selected = new Date(viewYear, viewMonth, day);
    selected.setHours(0, 0, 0, 0);
    if (selected < minD) return;
    const iso = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    onChange(iso);
    setOpen(false);
  }

  function isSelected(day: number) {
    if (!value) return false;
    const v = new Date(value + "T00:00:00");
    return v.getFullYear() === viewYear && v.getMonth() === viewMonth && v.getDate() === day;
  }

  function isDisabled(day: number) {
    const d = new Date(viewYear, viewMonth, day);
    d.setHours(0, 0, 0, 0);
    return d < minD;
  }

  const cells = buildCalendar();
  const displayValue = value
    ? new Date(value + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
    : "Select date";

  return (
    <>
      <Text style={styles.label}>{label}</Text>
      <TouchableOpacity style={styles.input} onPress={() => setOpen(true)}>
        <Text style={value ? styles.valueText : styles.placeholderText}>
          {displayValue}
        </Text>
      </TouchableOpacity>

      <Modal visible={open} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modal}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>{label}</Text>
            <TouchableOpacity onPress={() => setOpen(false)}>
              <Text style={styles.cancel}>Cancel</Text>
            </TouchableOpacity>
          </View>

          {/* Month navigation */}
          <View style={styles.navRow}>
            <TouchableOpacity style={styles.navBtn} onPress={prevMonth}>
              <Text style={styles.navArrow}>‹</Text>
            </TouchableOpacity>
            <Text style={styles.monthYear}>
              {MONTHS[viewMonth]} {viewYear}
            </Text>
            <TouchableOpacity style={styles.navBtn} onPress={nextMonth}>
              <Text style={styles.navArrow}>›</Text>
            </TouchableOpacity>
          </View>

          {/* Day headers */}
          <View style={styles.weekRow}>
            {DAYS.map((d) => (
              <Text key={d} style={styles.dayHeader}>{d}</Text>
            ))}
          </View>

          {/* Calendar grid */}
          <View style={styles.grid}>
            {cells.map((day, i) => {
              if (day === null) return <View key={`e-${i}`} style={styles.cell} />;
              const disabled = isDisabled(day);
              const selected = isSelected(day);
              return (
                <TouchableOpacity
                  key={`d-${day}`}
                  style={[styles.cell, selected && styles.selectedCell]}
                  onPress={() => selectDay(day)}
                  disabled={disabled}
                >
                  <Text
                    style={[
                      styles.dayText,
                      disabled && styles.disabledDay,
                      selected && styles.selectedDay,
                    ]}
                  >
                    {day}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </Modal>
    </>
  );
}

const CELL_SIZE = 44;

const styles = StyleSheet.create({
  label: {
    fontSize: FontSize.xs,
    fontWeight: "700",
    color: Colors.gray[300],
    letterSpacing: 1.5,
    marginBottom: Spacing.xs,
    marginTop: Spacing.sm,
  },
  input: {
    backgroundColor: Colors.navy[700],
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.xs,
  },
  valueText: { color: Colors.white, fontSize: FontSize.md, fontWeight: "600" },
  placeholderText: { color: Colors.gray[500], fontSize: FontSize.md },
  modal: { flex: 1, backgroundColor: Colors.navy[950] },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: Spacing.lg,
    paddingTop: Spacing.xl,
    borderBottomWidth: 1,
    borderBottomColor: Colors.navy[700],
  },
  headerTitle: { fontSize: FontSize.lg, fontWeight: "700", color: Colors.white },
  cancel: { color: Colors.orange[400], fontSize: FontSize.md },
  navRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
  },
  navBtn: {
    padding: Spacing.sm,
    backgroundColor: Colors.navy[800],
    borderRadius: BorderRadius.md,
    minWidth: 40,
    alignItems: "center",
  },
  navArrow: { color: Colors.white, fontSize: 24, fontWeight: "300" },
  monthYear: { color: Colors.white, fontSize: FontSize.lg, fontWeight: "700" },
  weekRow: {
    flexDirection: "row",
    paddingHorizontal: Spacing.md,
    marginBottom: Spacing.xs,
  },
  dayHeader: {
    width: CELL_SIZE,
    textAlign: "center",
    color: Colors.gray[500],
    fontSize: FontSize.xs,
    fontWeight: "700",
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: Spacing.md,
  },
  cell: {
    width: CELL_SIZE,
    height: CELL_SIZE,
    justifyContent: "center",
    alignItems: "center",
    borderRadius: CELL_SIZE / 2,
    margin: 1,
  },
  selectedCell: { backgroundColor: Colors.orange[500] },
  dayText: { color: Colors.white, fontSize: FontSize.md },
  disabledDay: { color: Colors.navy[600] },
  selectedDay: { color: Colors.white, fontWeight: "800" },
});
